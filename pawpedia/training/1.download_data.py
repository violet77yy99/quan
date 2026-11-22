# -*- coding: utf-8 -*-
"""
1.download_data.py
------------------
百度图片爬虫：按类别下载犬类品种图片（含 1 个橘猫干扰类）。

类别（文件夹名 -> 搜索关键词）：
    比格      -> 比格犬
    中华田园犬 -> 中华田园犬
    泰迪      -> 泰迪犬
    萨摩耶    -> 萨摩耶犬
    橘猫      -> 橘猫      （负样本/干扰项）
    边牧      -> 边境牧羊犬
    金毛      -> 金毛犬
    柯基      -> 柯基犬

每类目标 300 张（可在 TARGET_PER_CLASS 修改）。

运行方式（必须在 dog_recognition/ 目录下）：
    python 1.download_data.py

实现要点：
1. 先访问图片搜索首页拿 BAIDUID Cookie，再请求 acjson 接口；
   不带 Cookie 时服务端直接返回 {"antiFlag":1,"message":"Forbid spider access"}。
2. 接口参数：tn=resultjson_com & word=关键词 & pn=偏移量 & rn=30 & ala=0 & nojc=0 & newReq=1
3. 优先取 thumburl（百度 CDN 缩略图，稳定、无防盗链），取不到再取 objurl。
4. 下载后立即用 PIL 校验 + 去重（MD5），损坏图/过小图直接删除。
5. 每张图间隔 0.2s、每页间隔 1.2s，降低触发反爬的概率。
"""

import hashlib
import os
import sys
import time

# Windows 控制台/重定向默认可能是 GBK，统一改为 UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from urllib.parse import quote

import requests
from PIL import Image

# ==================== 配置区 ====================

SAVE_ROOT = "./dog_images"          # 原始图片根目录
TARGET_PER_CLASS = 300              # 每类目标图片数
MAX_PAGES = 25                      # 最多翻 25 页（25 × 30 = 750 条候选链接）
PAGE_SIZE = 30                      # 每页条数，接口固定 30
PAGE_INTERVAL = 1.2                 # 翻页间隔（秒）
IMAGE_INTERVAL = 0.2                # 单张下载间隔（秒）
MIN_SIDE = 100                      # 最短边小于 100px 的图片丢弃
MIN_FILE_SIZE = 5 * 1024            # 小于 5KB 的文件丢弃

CATEGORIES = [
    ("比格", "比格犬"),
    ("中华田园犬", "中华田园犬"),
    ("泰迪", "泰迪犬"),
    ("萨摩耶", "萨摩耶犬"),
    ("橘猫", "橘猫"),
    ("边牧", "边境牧羊犬"),
    ("金毛", "金毛犬"),
    ("柯基", "柯基犬"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36"
    ),
    "Referer": "https://image.baidu.com/",
    "X-Requested-With": "XMLHttpRequest",
}

# ==================== 爬虫实现 ====================


class BaiduImageSpider:
    """单类别图片爬虫。"""

    def __init__(self, name, keyword, save_dir):
        self.name = name                # 文件夹名，如“比格”
        self.keyword = keyword          # 搜索关键词，如“比格犬”
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        self._clean_stale_temp_files()
        self.seen_urls = set()          # 本次运行内 URL 去重
        self.seen_hashes = self._load_existing_hashes()  # 内容去重
        self.next_index = self._next_file_index()
        self.count = self._count_existing()

    def _clean_stale_temp_files(self):
        """清理上次中断留下的 .tmp_*.part 临时文件。"""
        for name in os.listdir(self.save_dir):
            if name.startswith(".tmp_") and name.endswith(".part"):
                try:
                    os.remove(os.path.join(self.save_dir, name))
                except OSError:
                    pass

    # ---------- 文件/去重辅助 ----------

    def _image_files(self):
        return [
            f for f in os.listdir(self.save_dir)
            if os.path.isfile(os.path.join(self.save_dir, f))
            and os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ]

    def _next_file_index(self):
        prefix = self.name + "_"
        max_idx = 0
        for f in self._image_files():
            if f.startswith(prefix):
                stem = os.path.splitext(f)[0][len(prefix):]
                if stem.isdigit():
                    max_idx = max(max_idx, int(stem))
        return max_idx + 1

    def _count_existing(self):
        return len(self._image_files())

    def _load_existing_hashes(self):
        """计算已有图片的 MD5，避免重复运行时重复落盘。"""
        hashes = set()
        for f in self._image_files():
            path = os.path.join(self.save_dir, f)
            try:
                hashes.add(self._file_md5(path))
            except OSError:
                pass
        return hashes

    @staticmethod
    def _file_md5(path):
        md5 = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                md5.update(chunk)
        return md5.hexdigest()

    # ---------- 网络请求 ----------

    def warm_up(self):
        """访问搜索首页，获取 BAIDUID Cookie（不带 Cookie 会被反爬拦截）。"""
        url = "https://image.baidu.com/search/index?tn=baiduimage&word=" + quote(self.keyword)
        try:
            self.session.get(url, timeout=15)
            time.sleep(0.5)
        except requests.RequestException as exc:
            print(f"  [警告] 首页预热失败：{exc}")

    @staticmethod
    def fix_image_url(url):
        """补全协议头，http 统一升级为 https。"""
        if not url or not isinstance(url, str):
            return None
        url = url.strip()
        if not url:
            return None
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("http://"):
            return "https://" + url[len("http://"):]
        if not url.startswith("http"):
            return "https://" + url
        return url

    def get_image_urls(self, page):
        """请求第 page 页，解析出图片直链列表。"""
        pn = page * PAGE_SIZE
        url = "https://image.baidu.com/search/acjson"
        params = {
            "tn": "resultjson_com",
            "word": self.keyword,
            "pn": pn,
            "rn": PAGE_SIZE,
            "ala": "0",
            "nojc": "0",
            "newReq": "1",
        }

        try:
            resp = self.session.get(url, params=params, timeout=15)
        except requests.RequestException as exc:
            print(f"  [警告] 第 {page + 1} 页请求失败：{exc}")
            return []

        if resp.status_code != 200:
            print(f"  [警告] 第 {page + 1} 页 HTTP {resp.status_code}")
            return []

        try:
            data = resp.json()
        except ValueError:
            print(f"  [警告] 第 {page + 1} 页返回的不是 JSON")
            return []

        if data.get("antiFlag"):
            print(f"  [警告] 被反爬拦截：{data.get('message')}")
            return []

        # 新版接口：data 是字典，图片列表在 data["images"]
        # 旧版接口：data 直接是列表（这里做兼容）
        payload = data.get("data")
        if isinstance(payload, dict):
            items = payload.get("images") or []
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

        urls = []
        for item in items:
            if not isinstance(item, dict):
                continue
            raw = (
                item.get("thumburl")
                or item.get("middleURL")
                or item.get("objurl")
                or item.get("hoverURL")
                or item.get("objURL")
            )
            fixed = self.fix_image_url(raw)
            if fixed and fixed not in self.seen_urls:
                self.seen_urls.add(fixed)
                urls.append(fixed)
        return urls

    # ---------- 下载与校验 ----------

    def download_image(self, img_url):
        """下载单张图片；成功返回 True。"""
        try:
            resp = self.session.get(
                img_url,
                headers={"User-Agent": HEADERS["User-Agent"]},
                stream=True,
                timeout=15,
            )
        except requests.RequestException:
            return False

        if resp.status_code != 200:
            return False

        content_type = resp.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            return False  # 链接失效时服务器会返回 HTML 错误页

        tmp_path = os.path.join(self.save_dir, f".tmp_{os.getpid()}.part")
        try:
            with open(tmp_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)

            if os.path.getsize(tmp_path) < MIN_FILE_SIZE:
                os.remove(tmp_path)
                return False

            # 内容去重：同一张图在不同页/不同关键词下只保留一份
            digest = self._file_md5(tmp_path)
            if digest in self.seen_hashes:
                os.remove(tmp_path)
                return False

            # 用 PIL 校验格式与尺寸（能否正常解码、是否过小）
            try:
                with open(tmp_path, "rb") as fh:
                    img = Image.open(fh)
                    img.verify()
                with open(tmp_path, "rb") as fh:
                    img = Image.open(fh)
                    width, height = img.size
            except Exception:
                os.remove(tmp_path)
                return False

            if min(width, height) < MIN_SIDE:
                os.remove(tmp_path)
                return False

            final_path = os.path.join(self.save_dir, f"{self.name}_{self.next_index}.jpg")
            os.replace(tmp_path, final_path)
            self.next_index += 1
            self.count += 1
            self.seen_hashes.add(digest)
            return True

        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # ---------- 主流程 ----------

    def run(self, target):
        """爬到目标数量或页数用尽为止，返回本次新增数量。"""
        if self.count >= target:
            print(f"  「{self.name}」已有 {self.count} 张，达到目标 {target}，跳过。")
            return 0

        downloaded = 0
        for page in range(MAX_PAGES):
            if self.count >= target:
                break

            urls = self.get_image_urls(page)
            if not urls and page == 0:
                # 首次请求可能 Cookie 尚未生效，重新预热后再试一次
                self.warm_up()
                urls = self.get_image_urls(page)

            if not urls:
                print(f"  第 {page + 1} 页没有可用链接，停止该类爬取。")
                break

            for img_url in urls:
                if self.count >= target:
                    break
                if self.download_image(img_url):
                    downloaded += 1
                    if downloaded % 20 == 0:
                        print(f"  已新增 {downloaded} 张（目录共 {self.count} 张）")
                time.sleep(IMAGE_INTERVAL)

            time.sleep(PAGE_INTERVAL)

        return downloaded


def main():
    print("=" * 60)
    print("开始爬取犬类品种图片（8 类，每类目标 300 张）")
    print("=" * 60)

    total_new = 0
    summary = []

    for name, keyword in CATEGORIES:
        save_dir = os.path.join(SAVE_ROOT, name)
        print(f"\n========== 开始爬取「{name}」（关键词：{keyword}）==========")

        spider = BaiduImageSpider(name, keyword, save_dir)
        spider.warm_up()
        added = spider.run(TARGET_PER_CLASS)
        total_new += added
        summary.append((name, spider.count, added))
        print(f"「{name}」本次新增 {added} 张，目录现有 {spider.count} 张。")

        time.sleep(2)

    print("\n" + "=" * 60)
    print("爬取完成，统计：")
    for name, total, added in summary:
        print(f"  {name:<8} 共 {total:>4} 张（本次新增 {added} 张）")
    print(f"本次合计新增：{total_new} 张")
    print(f"图片保存目录：{os.path.abspath(SAVE_ROOT)}")
    print("=" * 60)


if __name__ == "__main__":
    main()