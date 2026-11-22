# -*- coding: utf-8 -*-
"""
3.train_cnn.py
--------------
训练犬类品种分类 CNN（DogCNN）。

输入：./dog_images_split/{train,test}/<类别>/
输出：
    ./models/dog_classification_model.pth   模型权重 + 类别名 + 训练历史
    ./results/training_history.png          训练曲线
    ./results/prediction_<类别>.png         单张测试图预测可视化

运行方式（必须在 dog_recognition/ 目录下）：
    python 3.train_cnn.py

模型结构（与参考项目保持一致）：
    输入 [3,128,128]
    Conv(3→32)+ReLU+Pool → [32,64,64]
    Conv(32→64)+ReLU+Pool → [64,32,32]
    Conv(64→128)+ReLU+Pool → [128,16,16]
    Conv(128→128)+ReLU+Pool → [128,8,8]
    Flatten → Dropout → Linear(8192→256) → ReLU → Dropout → Linear(256→8)

注意：若修改 IMG_SIZE 或网络结构，界面脚本里的 DogCNN 必须同步修改。
"""

import os
import random
import sys
import time

# Windows 控制台/重定向默认可能是 GBK，统一改为 UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")          # 无 GUI 环境也能画图，只保存文件不弹窗
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from tqdm import tqdm

# ==================== 配置区 ====================

DATA_ROOT = "./dog_images_split"
MODEL_DIR = "./models"
MODEL_PATH = os.path.join(MODEL_DIR, "dog_classification_model.pth")
RESULTS_DIR = "./results"          # 训练曲线、预测可视化、分析图统一放这里

IMG_SIZE = 128
BATCH_SIZE = 32
EPOCHS = 60
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.0
LABEL_SMOOTHING = 0.0
NUM_WORKERS = 0                # Windows 下必须为 0
RANDOM_SEED = 42
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# matplotlib 中文字体（Windows 一般自带微软雅黑）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ==================== 数据加载 ====================


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def is_valid_image(path):
    """检查文件是否为可正常解码、尺寸不小于 32×32 的图片。"""
    try:
        with open(path, "rb") as f:
            Image.open(f).verify()          # 只校验文件头，速度快
        with open(path, "rb") as f:
            img = Image.open(f)
            width, height = img.size
        return width >= 32 and height >= 32
    except Exception:
        return False


def collect_samples(folder, class_to_idx, tag):
    """扫描一个文件夹，返回 [(图片路径, 类别索引), ...]。"""
    samples = []
    skipped = 0
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in VALID_EXTS:
            continue
        if not is_valid_image(path):
            skipped += 1
            print(f"  [跳过] 损坏/过小图片：{path}")
            continue
        category = os.path.basename(folder)
        samples.append((path, class_to_idx[category]))
    if skipped:
        print(f"  {tag}：跳过 {skipped} 张无效图片")
    return samples


class DogDataset(Dataset):
    """按需读取图片（不在内存里常驻全部解码结果）。"""

    def __init__(self, samples, transform, name="dataset"):
        self.samples = samples
        self.transform = transform
        self.name = name
        self.bad_count = 0

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, label = self.samples[index]
        try:
            with open(path, "rb") as f:
                image = Image.open(f).convert("RGB")   # 灰度/RGBA 统一转三通道
        except Exception:
            self.bad_count += 1
            image = Image.new("RGB", (IMG_SIZE, IMG_SIZE))   # 兜底，避免训练中断
        if self.transform is not None:
            image = self.transform(image)
        return image, label


# 训练集：随机增强（只用于训练）
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(20),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# 测试集/推理：只缩放 + 标准化，绝不能加随机增强
test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ==================== 模型定义 ====================


class DogCNN(nn.Module):
    """4 层卷积 + 2 层全连接的轻量 CNN。"""

    def __init__(self, num_classes=8):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                 # 128 → 64

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                 # 64 → 32

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                 # 32 → 16

            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                 # 16 → 8
        )
        # 128 × 8 × 8 = 8192；输入尺寸改动时这里必须同步改
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


# ==================== 训练与评估 ====================


def train_one_epoch(model, loader, criterion, optimizer, device, epoch):
    model.train()            # 开启 Dropout 训练模式
    running_loss = 0.0
    correct = 0
    total = 0

    progress = tqdm(loader, desc=f"Epoch {epoch}/{EPOCHS} [Train]", ncols=100, leave=False)
    for images, labels in progress:
        images, labels = images.to(device), labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()    # 1. 清空上批梯度
        loss.backward()          # 2. 反向传播
        optimizer.step()         # 3. 更新参数

        running_loss += loss.item() * images.size(0)   # 按样本数加权
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        progress.set_postfix(
            loss=f"{running_loss / max(total, 1):.4f}",
            acc=f"{correct / max(total, 1):.4f}",
        )

    return running_loss / max(total, 1), correct / max(total, 1)


def evaluate(model, loader, criterion, device, desc="Test"):
    model.eval()             # 关闭 Dropout
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():    # 验证阶段不建计算图，节省内存
        for images, labels in tqdm(loader, desc=desc, ncols=100, leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    return running_loss / max(total, 1), correct / max(total, 1)


def print_confusion_matrix(model, loader, device, class_names):
    """在测试集上统计混淆矩阵与各类准确率。"""
    model.eval()
    size = len(class_names)
    matrix = [[0] * size for _ in range(size)]

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            preds = model(images).argmax(dim=1).cpu()
            for true_idx, pred_idx in zip(labels.tolist(), preds.tolist()):
                matrix[true_idx][pred_idx] += 1

    print("\n混淆矩阵（行 = 真实类别，列 = 预测类别）：")
    print("真实\\预测".ljust(12) + "".join(f"{name:>10}" for name in class_names))
    for i, name in enumerate(class_names):
        print(f"{name:<12}" + "".join(f"{value:>10}" for value in matrix[i]))

    print("\n各类准确率：")
    for i, name in enumerate(class_names):
        total = sum(matrix[i])
        correct = matrix[i][i]
        acc = correct / total if total else 0.0
        print(f"  {name:<8} {correct}/{total} = {acc:.0%}")

    return matrix


# ==================== 可视化 ====================


def plot_history(history, save_path):
    """保存准确率/损失曲线；失败时打印文本表格作为兜底。"""
    try:
        epochs = range(1, len(history["train_loss"]) + 1)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

        axes[0].plot(epochs, history["train_acc"], "o-", label="训练准确率", color="#2E86DE")
        axes[0].plot(epochs, history["test_acc"], "s-", label="测试准确率", color="#EE5A24")
        axes[0].set_title("准确率曲线")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Accuracy")
        axes[0].grid(alpha=0.3)
        axes[0].legend()

        axes[1].plot(epochs, history["train_loss"], "o-", label="训练损失", color="#2E86DE")
        axes[1].plot(epochs, history["test_loss"], "s-", label="测试损失", color="#EE5A24")
        axes[1].set_title("损失曲线")
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("Loss")
        axes[1].grid(alpha=0.3)
        axes[1].legend()

        fig.suptitle("犬类品种分类模型训练曲线", fontsize=14)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"训练曲线已保存：{os.path.abspath(save_path)}")
    except Exception as exc:
        print(f"训练曲线保存失败：{exc}")
        print("Epoch | TrainLoss | TrainAcc | TestLoss | TestAcc")
        for i in range(len(history["train_loss"])):
            print(
                f"{i + 1:>5} | {history['train_loss'][i]:.4f}    | "
                f"{history['train_acc'][i]:.4f}   | {history['test_loss'][i]:.4f}   | "
                f"{history['test_acc'][i]:.4f}"
            )


def find_demo_image():
    """优先拿测试集里「比格」的第一张图做预测演示。"""
    preferred = os.path.join(DATA_ROOT, "test", "比格")
    if os.path.isdir(preferred):
        images = sorted(
            f for f in os.listdir(preferred)
            if os.path.splitext(f)[1].lower() in VALID_EXTS
        )
        if images:
            return os.path.join(preferred, images[0]), "比格"

    test_root = os.path.join(DATA_ROOT, "test")
    for category in sorted(os.listdir(test_root)):
        folder = os.path.join(test_root, category)
        if not os.path.isdir(folder):
            continue
        images = sorted(
            f for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in VALID_EXTS
        )
        if images:
            return os.path.join(folder, images[0]), category
    return None, None


def save_prediction_demo(model, class_names, device):
    """对一张测试图做预测，并把原图 + 预测结果保存成 PNG。"""
    image_path, true_label = find_demo_image()
    if image_path is None:
        print("未找到可用于演示的测试图片，跳过预测可视化。")
        return

    image = Image.open(image_path).convert("RGB")
    tensor = test_transform(image).unsqueeze(0).to(device)   # [1,3,128,128]

    model.eval()
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, pred_idx = torch.max(probs, 1)

    pred_label = class_names[pred_idx.item()]
    confidence = confidence.item() * 100

    try:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        fig, ax = plt.subplots(figsize=(7, 5.5))
        ax.imshow(image)
        ax.axis("off")
        ax.set_title(
            f"预测结果：{pred_label}（置信度 {confidence:.2f}%）\n真实类别：{true_label}",
            fontsize=13,
        )
        save_path = os.path.join(RESULTS_DIR, f"prediction_{pred_label}.png")
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"单张预测结果：{pred_label}（{confidence:.2f}%），已保存 {os.path.abspath(save_path)}")
    except Exception as exc:
        print(f"预测可视化保存失败：{exc}")
        print(f"单张预测结果：{pred_label}（置信度 {confidence:.2f}%）")


# ==================== 主流程 ====================


def main():
    set_seed(RANDOM_SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用计算设备：{device}")

    train_root = os.path.join(DATA_ROOT, "train")
    test_root = os.path.join(DATA_ROOT, "test")
    if not os.path.isdir(train_root) or not os.path.isdir(test_root):
        print("未找到划分后的数据集目录！")
        print("请先运行：python 2.split_data.py")
        return

    # 类别顺序由文件夹名 Unicode 排序决定，训练/测试必须一致
    class_names = sorted(
        name for name in os.listdir(train_root)
        if os.path.isdir(os.path.join(train_root, name))
    )
    if not class_names:
        print("训练集下没有任何类别文件夹，请检查数据集。")
        return

    test_classes = sorted(
        name for name in os.listdir(test_root)
        if os.path.isdir(os.path.join(test_root, name))
    )
    if class_names != test_classes:
        print("训练集与测试集的类别文件夹不一致！")
        print(f"训练集：{class_names}")
        print(f"测试集：{test_classes}")
        return

    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    print("类别顺序（索引 → 名称）：")
    for idx, name in enumerate(class_names):
        print(f"  {idx} → {name}")

    print("\n正在扫描并校验图片...")
    train_samples = []
    for category in class_names:
        folder = os.path.join(train_root, category)
        samples = collect_samples(folder, class_to_idx, f"训练集/{category}")
        train_samples.extend(samples)
        print(f"  训练集「{category}」：{len(samples)} 张")

    test_samples = []
    for category in class_names:
        folder = os.path.join(test_root, category)
        samples = collect_samples(folder, class_to_idx, f"测试集/{category}")
        test_samples.extend(samples)
        print(f"  测试集「{category}」：{len(samples)} 张")

    if not train_samples or not test_samples:
        print("训练集或测试集为空，无法训练。")
        return

    train_dataset = DogDataset(train_samples, train_transform, name="train")
    test_dataset = DogDataset(test_samples, test_transform, name="test")
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS
    )
    test_loader = DataLoader(
        test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS
    )

    model = DogCNN(num_classes=len(class_names)).to(device)
    print("\n模型结构：")
    print(model)

    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
    optimizer = optim.Adam(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    # 每 20 个 epoch 学习率减半，后期更稳定
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)

    history = {
        "train_loss": [], "train_acc": [],
        "test_loss": [], "test_acc": [],
    }
    best_acc = 0.0
    best_epoch = 0
    best_state = None

    print(f"\n开始训练（{EPOCHS} epochs）...")
    start_time = time.time()
    for epoch in range(1, EPOCHS + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )
        test_loss, test_acc = evaluate(model, test_loader, criterion, device, desc="Test")

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["test_loss"].append(test_loss)
        history["test_acc"].append(test_acc)

        scheduler.step()

        if test_acc > best_acc:
            best_acc = test_acc
            best_epoch = epoch
            # 只保留最优权重（CPU 副本），训练结束后保存它
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

        print(f"Epoch {epoch} 总结：")
        print(f"  训练损失: {train_loss:.4f} | 训练准确率: {train_acc:.4f}")
        print(f"  测试损失: {test_loss:.4f} | 测试准确率: {test_acc:.4f}")

    elapsed = time.time() - start_time
    last_acc = history["test_acc"][-1]

    if best_state is not None:
        model.load_state_dict(best_state)      # 回滚到测试准确率最高的权重
    final_loss, final_acc = evaluate(model, test_loader, criterion, device, desc="Best model")
    print(f"\n最后一轮测试准确率：{last_acc:.4f}")
    print(f"保存的最优模型测试准确率：{final_acc:.4f} "
          f"({int(round(final_acc * len(test_samples)))}/{len(test_samples)})，Epoch {best_epoch}")
    print(f"训练总耗时：{elapsed / 60:.1f} 分钟（{elapsed:.0f} 秒）")

    print_confusion_matrix(model, test_loader, device, class_names)

    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "class_names": class_names,          # ★ 预测时必须使用同一顺序
            "final_accuracy": final_acc,          # 保存的最优模型准确率
            "best_test_acc": best_acc,
            "best_epoch": best_epoch,
            "last_test_acc": last_acc,        # 最后一轮的准确率（用于对比过拟合）
            "epochs": EPOCHS,
            "input_size": IMG_SIZE,
            "training_time_sec": elapsed,
            "history": history,
        },
        MODEL_PATH,
    )
    print(f"模型已保存为：{os.path.abspath(MODEL_PATH)}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    plot_history(history, os.path.join(RESULTS_DIR, "training_history.png"))
    save_prediction_demo(model, class_names, device)

    print("\n全部完成。下一步运行：python 4.classifier_ui.py")


if __name__ == "__main__":
    main()