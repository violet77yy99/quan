# -*- coding: utf-8 -*-
"""
2.split_data.py
---------------
把 ./dog_images 下按类别存放的原始图片，按 8:2 划分到：
    ./dog_images_split/train/<类别>/
    ./dog_images_split/test/<类别>/

运行方式（必须在 dog_recognition/ 目录下）：
    python 2.split_data.py

要点：
1. 固定随机种子 42，保证每次划分结果完全一致（可复现）。
2. 逐类别划分，而不是整体打乱，避免某些类别全进训练集。
3. 使用 os.listdir + 后缀集合收集图片，而不是按后缀反复 glob
   —— Windows 上 fnmatch 不区分大小写，*.jpg 和 *.JPG 会匹配同一批文件，导致数量翻倍。
4. 使用 shutil.copy2 复制（保留原图，方便重复实验）。
5. 每次运行先清空 dog_images_split/，避免上一次的旧文件残留。
"""

import os
import random
import shutil
import sys

# Windows 控制台/重定向默认可能是 GBK，统一改为 UTF-8，避免 emoji 引发 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==================== 配置区 ====================

SOURCE_DIR = "./dog_images"
TARGET_DIR = "./dog_images_split"
TRAIN_RATIO = 0.8
RANDOM_SEED = 42
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

EMOJI = "🐶"


def list_images(folder):
    """列出文件夹内所有合法图片（后缀转小写后判断，Windows 下不会重复计数）。"""
    return [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, name))
        and os.path.splitext(name)[1].lower() in VALID_EXTS
    ]


def reset_split_dir(target_dir):
    """清空上一次的划分结果，保证目录内容与本次划分一致。"""
    for subset in ("train", "test"):
        path = os.path.join(target_dir, subset)
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)


def split_dataset():
    if not os.path.isdir(SOURCE_DIR):
        print(f"未找到原始数据目录：{SOURCE_DIR}")
        print("请先运行 python 1.download_data.py 采集图片。")
        return

    categories = sorted(
        name for name in os.listdir(SOURCE_DIR)
        if os.path.isdir(os.path.join(SOURCE_DIR, name))
    )
    if not categories:
        print(f"{SOURCE_DIR} 下没有任何类别文件夹，请先采集图片。")
        return

    reset_split_dir(TARGET_DIR)
    random.seed(RANDOM_SEED)  # 固定种子：每次划分结果一致

    print("=" * 60)
    print(f"开始划分训练集/测试集（{round(TRAIN_RATIO * 10)}:{round((1 - TRAIN_RATIO) * 10)}，随机种子 {RANDOM_SEED}）")
    print("=" * 60)

    total_train = total_test = 0
    stats = []

    for category in categories:
        source_path = os.path.join(SOURCE_DIR, category)
        images = list_images(source_path)
        if not images:
            print(f"{EMOJI}「{category}」：没有找到图片，跳过。")
            continue

        random.shuffle(images)
        split_idx = int(len(images) * TRAIN_RATIO)
        train_images = images[:split_idx]
        test_images = images[split_idx:]

        train_dir = os.path.join(TARGET_DIR, "train", category)
        test_dir = os.path.join(TARGET_DIR, "test", category)
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)

        for img_path in train_images:
            shutil.copy2(img_path, os.path.join(train_dir, os.path.basename(img_path)))
        for img_path in test_images:
            shutil.copy2(img_path, os.path.join(test_dir, os.path.basename(img_path)))

        total_train += len(train_images)
        total_test += len(test_images)
        stats.append((category, len(images), len(train_images), len(test_images)))
        print(
            f"{EMOJI}「{category}」：总 {len(images)} 张 → "
            f"训练集 {len(train_images)} 张 | 测试集 {len(test_images)} 张"
        )

    print("\n" + "=" * 60)
    print("数据集划分完成")
    print(f"整体统计：训练集 {total_train} 张 | 测试集 {total_test} 张")
    print(f"输出目录：{os.path.abspath(TARGET_DIR)}")
    print("=" * 60)

    # 数据量过少的类别给出提醒
    for category, total, train_n, test_n in stats:
        if total < 50:
            print(f"⚠️ 「{category}」只有 {total} 张，建议补到 100 张以上再训练。")
        if test_n == 0:
            print(f"⚠️ 「{category}」测试集为 0 张，请增加该类图片数量。")


if __name__ == "__main__":
    split_dataset()