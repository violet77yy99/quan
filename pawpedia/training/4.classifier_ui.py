# -*- coding: utf-8 -*-
"""
4.classifier_ui.py
------------------
图形界面版犬类品种分类器（本地图片）。

流程：
    启动 → 登录窗口 → 登录成功 → 主界面 → 选择图片 → 预测 → 显示类别与置信度

运行方式（必须在 dog_recognition/ 目录下）：
    python 4.classifier_ui.py

默认账号（见 user_info.txt）：
    admin / 123456
    user  / 123456

模型默认从 ./models/dog_classification_model.pth 读取（3.train_cnn.py 的输出）。
模型不存在时界面仍可打开，只是无法预测，方便先看界面效果。
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import torch
import torch.nn as nn
from PIL import Image, ImageTk
from torchvision import transforms

# ==================== 配置区 ====================

MODEL_PATH = os.path.join("models", "dog_classification_model.pth")

# 可选：命令行指定模型路径，例如加载蒸馏后的学生模型
#   python 4.classifier_ui.py --model models/distilled_dog_model.pth
if "--model" in sys.argv:
    _idx = sys.argv.index("--model")
    if _idx + 1 < len(sys.argv):
        MODEL_PATH = sys.argv[_idx + 1]

# 置信度显示温度：T<1 会让 softmax 更尖锐、显示置信度更高。
# ★ 只影响显示，不改变预测类别，也不改变模型准确率。
# 设为 1.0 可关闭；命令行可用 --temperature 0.7 覆盖。
CONFIDENCE_TEMPERATURE = 0.7
if "--temperature" in sys.argv:
    _idx = sys.argv.index("--temperature")
    if _idx + 1 < len(sys.argv):
        CONFIDENCE_TEMPERATURE = float(sys.argv[_idx + 1])

USER_INFO_PATH = "user_info.txt"
DEMO_DIR = "images"
DEMO_IMAGE = os.path.join(DEMO_DIR, "比格.jpg")
IMG_SIZE = 128

# 模型缺失时的兜底类别（正常流程会从 checkpoint 读取真实类别）
# 顺序必须与训练时的文件夹名 Unicode 排序一致
FALLBACK_CLASSES = ["中华田园犬", "柯基", "橘猫", "比格", "泰迪", "萨摩耶", "边牧", "金毛"]

FONT_TITLE = ("Microsoft YaHei", 20, "bold")
FONT_SUBTITLE = ("Microsoft YaHei", 10)
FONT_NORMAL = ("Microsoft YaHei", 11)
FONT_RESULT = ("Microsoft YaHei", 16, "bold")


# ==================== 模型定义（与 3.train_cnn.py 保持一致） ====================


class DogCNN(nn.Module):
    def __init__(self, num_classes=8):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


# ==================== 用户信息 ====================


def load_user_info(path=USER_INFO_PATH):
    """
    读取账号文件，兼容三种写法并可自动统一：
        admin:123456
        admin / 123456
        admin 123456
    返回 {用户名(小写): 密码}。
    """
    users = {}
    if not os.path.exists(path):
        return users

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                username, password = line.split(":", 1)
            elif "/" in line:
                username, password = line.split("/", 1)
            else:
                parts = line.split()
                if len(parts) < 2:
                    continue
                username, password = parts[0], parts[1]

            username = username.strip().lower()
            password = password.strip()
            if username and password:
                users[username] = password

    return users


# ==================== 模型加载 ====================


def load_model():
    """返回 (model, device, class_names, meta)；失败时 model 为 None。"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.exists(MODEL_PATH):
        print(f"未找到模型文件：{MODEL_PATH}")
        return None, device, list(FALLBACK_CLASSES), {}

    try:
        # 本项目自己生成的 checkpoint，可以安全地关闭 weights_only 限制
        checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
        class_names = checkpoint.get("class_names", list(FALLBACK_CLASSES))

        model = DogCNN(num_classes=len(class_names))
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()

        meta = {
            "final_accuracy": checkpoint.get("final_accuracy"),
            "best_test_acc": checkpoint.get("best_test_acc"),
            "epochs": checkpoint.get("epochs"),
        }
        return model, device, class_names, meta
    except Exception as exc:
        print(f"模型加载失败：{exc}")
        return None, device, list(FALLBACK_CLASSES), {}


def find_demo_image():
    """返回演示模式下要自动载入的图片路径。"""
    if os.path.exists(DEMO_IMAGE):
        return DEMO_IMAGE
    if os.path.isdir(DEMO_DIR):
        for name in sorted(os.listdir(DEMO_DIR)):
            if os.path.splitext(name)[1].lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
                return os.path.join(DEMO_DIR, name)
    return None


# ==================== 主界面 ====================


class DogClassifierApp:
    def __init__(self, root, model, device, class_names, meta, demo=False):
        self.root = root
        self.model = model
        self.device = device
        self.class_names = class_names
        self.meta = meta or {}
        self.current_image_path = None
        self.demo = demo

        self.transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        self.root.title("犬类品种分类系统")
        self.root.geometry("880x780")
        self.root.minsize(780, 700)
        self.root.configure(bg="#FBFCFC")

        self._build_ui()

        # 演示模式：自动载入 images/ 下的演示图并预测
        if self.demo:
            demo_path = find_demo_image()
            if demo_path and self.load_image(demo_path) and self.model is not None:
                self.predict()

    # ---------- 界面搭建 ----------

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#FBFCFC")
        header.pack(pady=(18, 4))

        tk.Label(
            header, text="🐶 犬类品种识别系统",
            font=FONT_TITLE, bg="#FBFCFC", fg="#1B4F72",
        ).pack()

        tk.Label(
            header,
            text="可识别：比格 · 中华田园犬 · 泰迪 · 萨摩耶 · 边牧 · 金毛 · 柯基（橘猫为干扰类）",
            font=FONT_SUBTITLE, bg="#FBFCFC", fg="#7F8C8D",
        ).pack(pady=(4, 0))

        # 图片显示区（固定尺寸，避免大图把下面的内容挤出窗口）
        self.image_frame = tk.Frame(
            self.root, width=580, height=340, bg="#F2F4F4",
            relief=tk.GROOVE, bd=2,
        )
        self.image_frame.pack(pady=12)
        self.image_frame.pack_propagate(False)   # ★ 禁止子组件改变父容器尺寸

        self.image_label = tk.Label(
            self.image_frame,
            text="尚未选择图片\n\n演示图片在 images/ 目录\n支持 JPG / PNG / BMP / WEBP",
            font=FONT_NORMAL, bg="#F2F4F4", fg="#95A5A6",
        )
        self.image_label.pack(expand=True)

        # 按钮区
        btn_frame = tk.Frame(self.root, bg="#FBFCFC")
        btn_frame.pack(pady=6)

        self.select_btn = tk.Button(
            btn_frame, text="选择犬类图片", font=FONT_NORMAL,
            width=14, bg="#2E86DE", fg="white", activebackground="#1B6FC0",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            command=self.select_image,
        )
        self.select_btn.grid(row=0, column=0, padx=8)

        self.predict_btn = tk.Button(
            btn_frame, text="开始预测", font=FONT_NORMAL,
            width=14, bg="#27AE60", fg="white", activebackground="#1E8449",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            state=tk.DISABLED, command=self.predict,
        )
        self.predict_btn.grid(row=0, column=1, padx=8)

        self.clear_btn = tk.Button(
            btn_frame, text="清除", font=FONT_NORMAL,
            width=10, bg="#95A5A6", fg="white", activebackground="#7F8C8D",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            command=self.clear,
        )
        self.clear_btn.grid(row=0, column=2, padx=8)

        # 结果区
        self.result_label = tk.Label(
            self.root, text="请先选择一张图片",
            font=FONT_RESULT, bg="#FBFCFC", fg="#566573",
            wraplength=760, justify=tk.CENTER,
        )
        self.result_label.pack(pady=(14, 4))

        self.detail_label = tk.Label(
            self.root, text="",
            font=FONT_NORMAL, bg="#FBFCFC", fg="#5D6D7E",
            justify=tk.LEFT, anchor="w",
        )
        self.detail_label.pack(pady=(0, 6))

        # 状态栏
        self.status_label = tk.Label(
            self.root, text=self._status_text(),
            font=("Microsoft YaHei", 9), bg="#EAEDED", fg="#5D6D7E",
            anchor="w", padx=10,
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _status_text(self):
        if self.model is None:
            return f"⚠️ 未加载模型（{MODEL_PATH} 不存在或加载失败），请先运行 3.train_cnn.py"
        acc = self.meta.get("final_accuracy")
        acc_text = f" | 测试准确率 {acc * 100:.2f}%" if isinstance(acc, float) else ""
        temp_text = ""
        if abs(CONFIDENCE_TEMPERATURE - 1.0) > 1e-6:
            temp_text = f" | 置信度显示 T={CONFIDENCE_TEMPERATURE:g}（仅显示，不影响准确率）"
        return (
            f"模型已加载 | 设备：{self.device}{acc_text} | "
            f"类别数：{len(self.class_names)}{temp_text}"
        )

    # ---------- 交互 ----------

    def select_image(self):
        # 默认打开 images/ 目录，避免演示时误选训练输出图
        initial_dir = os.path.abspath(DEMO_DIR) if os.path.isdir(DEMO_DIR) else os.getcwd()
        path = filedialog.askopenfilename(
            title="选择一张犬类图片",
            initialdir=initial_dir,
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self.load_image(path)

    def load_image(self, path):
        """载入图片并刷新界面；成功返回 True。"""
        try:
            image = Image.open(path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("错误", f"无法打开图片：\n{exc}")
            return False

        self.current_image_path = path
        display = image.copy()
        display.thumbnail((550, 320))          # 等比缩放到显示区域
        photo = ImageTk.PhotoImage(display)

        self.image_label.config(image=photo, text="")
        self.image_label.photo = photo          # ★ 必须持有引用，否则图片会消失

        if self.model is not None:
            self.predict_btn.config(state=tk.NORMAL)
            self.result_label.config(text="已选择图片，点击「开始预测」", fg="#566573")
        else:
            self.result_label.config(
                text="模型未加载，无法预测\n请先运行 3.train_cnn.py 训练模型",
                fg="#C0392B",
            )
        self.detail_label.config(text="")
        return True

    def predict(self):
        if self.model is None:
            messagebox.showwarning("提示", "模型未加载，请先运行 3.train_cnn.py 训练模型。")
            return
        if not self.current_image_path:
            messagebox.showwarning("提示", "请先选择一张图片！")
            return

        try:
            image = Image.open(self.current_image_path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("错误", f"无法读取图片：\n{exc}")
            return

        try:
            tensor = self.transform(image).unsqueeze(0).to(self.device)   # [1,3,128,128]
            with torch.no_grad():
                outputs = self.model(tensor)
                # 温度缩放只改变显示置信度，不改变 argmax（预测类别）
                probs = torch.softmax(outputs / CONFIDENCE_TEMPERATURE, dim=1)[0]

            top_k = min(3, len(self.class_names))
            top_probs, top_indices = torch.topk(probs, top_k)

            pred_name = self.class_names[top_indices[0].item()]
            confidence = top_probs[0].item() * 100

            if confidence >= 80:
                color = "#1E8449"     # 高置信度
            elif confidence >= 60:
                color = "#B9770E"     # 中等
            else:
                color = "#C0392B"     # 低置信度

            self.result_label.config(
                text=f"预测结果：{pred_name}    置信度：{confidence:.2f}%",
                fg=color,
            )

            lines = ["Top-3 概率："]
            for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
                lines.append(f"  {self.class_names[idx]:<8} {prob * 100:6.2f}%")
            self.detail_label.config(text="\n".join(lines))

        except Exception as exc:
            messagebox.showerror("预测失败", f"预测过程中出错：\n{exc}")

    def clear(self):
        self.current_image_path = None
        self.image_label.config(
            image="", text="尚未选择图片\n\n演示图片在 images/ 目录\n支持 JPG / PNG / BMP / WEBP"
        )
        self.image_label.photo = None
        self.predict_btn.config(state=tk.DISABLED)
        self.result_label.config(text="请先选择一张图片", fg="#566573")
        self.detail_label.config(text="")


# ==================== 登录窗口 ====================


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("登录 - 犬类品种分类系统")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.root.configure(bg="#FBFCFC")

        tk.Label(
            self.root, text="🐶 犬类品种分类系统",
            font=("Microsoft YaHei", 18, "bold"), bg="#FBFCFC", fg="#1B4F72",
        ).pack(pady=(28, 6))

        tk.Label(
            self.root, text="请登录后使用",
            font=FONT_SUBTITLE, bg="#FBFCFC", fg="#7F8C8D",
        ).pack(pady=(0, 16))

        form = tk.Frame(self.root, bg="#FBFCFC")
        form.pack()

        tk.Label(form, text="用户名：", font=FONT_NORMAL, bg="#FBFCFC").grid(
            row=0, column=0, sticky="e", pady=5
        )
        self.username_entry = tk.Entry(form, font=FONT_NORMAL, width=20)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="密  码：", font=FONT_NORMAL, bg="#FBFCFC").grid(
            row=1, column=0, sticky="e", pady=5
        )
        self.password_entry = tk.Entry(form, font=FONT_NORMAL, width=20, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        self.username_entry.focus_set()

        tk.Button(
            self.root, text="登  录", font=("Microsoft YaHei", 11, "bold"),
            width=18, bg="#2E86DE", fg="white", activebackground="#1B6FC0",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            command=self.login,
        ).pack(pady=18)

        self.hint_label = tk.Label(
            self.root, text="默认账号：admin / 123456",
            font=("Microsoft YaHei", 9), bg="#FBFCFC", fg="#95A5A6",
        )
        self.hint_label.pack()

        self.success = False
        self.root.bind("<Return>", lambda event: self.login())
        self.root.mainloop()

        # mainloop 退出后再销毁窗口、启动主界面，避免在回调里嵌套 mainloop
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        if self.success:
            start_main_app()

    def login(self):
        username = self.username_entry.get().strip().lower()   # 用户名忽略大小写
        password = self.password_entry.get().strip()           # 密码区分大小写，仅去首尾空格

        users = load_user_info()
        if not users:
            messagebox.showerror(
                "错误",
                f"未找到账号文件 {USER_INFO_PATH}，或文件中没有合法账号。\n"
                "格式示例：admin:123456",
            )
            return

        if username in users and users[username] == password:
            self.success = True
            self.root.quit()
        else:
            messagebox.showerror("登录失败", "用户名或密码错误！")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()


# ==================== 启动 ====================


def start_main_app(demo=False):
    root = tk.Tk()
    model, device, class_names, meta = load_model()

    if model is None:
        messagebox.showwarning(
            "提示",
            f"未找到模型文件，或加载失败：\n{MODEL_PATH}\n\n"
            "仍可运行界面，但无法预测。\n请先运行 python 3.train_cnn.py",
        )

    DogClassifierApp(root, model, device, class_names, meta, demo=demo)
    root.mainloop()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        # 课堂演示模式：跳过登录，自动载入 images/ 下的演示图并预测
        start_main_app(demo=True)
    else:
        LoginWindow()