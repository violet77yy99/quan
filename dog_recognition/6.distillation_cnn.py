# -*- coding: utf-8 -*-
"""
6.distillation_cnn.py
---------------------
知识蒸馏：教师模型（已训练好的 8 类 DogCNN）→ 学生模型（同结构 DogCNN）。

核心公式（标准写法）：

    Loss = α · T² · KL( softmax(student/T) ‖ softmax(teacher/T) )
           + (1 - α) · CrossEntropy(student, label)

- T（温度）：T 越大，教师输出的概率分布越平滑，类别间的“暗知识”越明显；
- α（软损失权重）：通常取 0.7 左右；α=1 表示只用教师软标签，α=0 退化为普通训练；
- 乘 T²：抵消温度对梯度尺度的缩放，让软损失和硬损失处于同一量级。

与参考文档 5.5 的差异：
    参考代码实际写成 `alpha * soft_loss + 1.0 * hard_loss`，且 alpha=2.0，
    不属于标准的 α∈[0,1] 写法。本脚本按论文/教材的标准公式实现：
    `alpha * soft_loss + (1 - alpha) * hard_loss`，默认 alpha=0.7、T=4。

输入：
    ./dog_images_split/{train,test}/<类别>/
    ./models/dog_classification_model.pth     教师模型（3.train_cnn.py 的输出）

输出：
    ./models/distilled_dog_model.pth          学生模型
    ./results/distillation_history.png        蒸馏训练曲线
    ./results/distillation_result.txt         教师/学生结果对比

运行方式（必须在 dog_recognition/ 目录下）：
    python 6.distillation_cnn.py
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
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from tqdm import tqdm

# ==================== 配置区 ====================

DATA_ROOT = "./dog_images_split"
MODEL_DIR = "./models"
RESULTS_DIR = "./results"

TEACHER_PATH = os.path.join(MODEL_DIR, "dog_classification_model.pth")
STUDENT_PATH = os.path.join(MODEL_DIR, "distilled_dog_model.pth")

IMG_SIZE = 128
BATCH_SIZE = 32
EPOCHS = int(os.environ.get("DISTILL_EPOCHS", "60"))
LEARNING_RATE = 0.001
TEMPERATURE = float(os.environ.get("DISTILL_T", "4.0"))     # 蒸馏温度 T
ALPHA = float(os.environ.get("DISTILL_ALPHA", "0.7"))       # 软损失权重，标准范围 [0, 1]
NUM_WORKERS = 0            # Windows 下必须为 0
RANDOM_SEED = 42
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

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
    try:
        with open(path, "rb") as f:
            Image.open(f).verify()
        with open(path, "rb") as f:
            img = Image.open(f)
            width, height = img.size
        return width >= 32 and height >= 32
    except Exception:
        return False


def collect_samples(folder, class_to_idx, tag):
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
    def __init__(self, samples, transform, name="dataset"):
        self.samples = samples
        self.transform = transform
        self.name = name

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, label = self.samples[index]
        try:
            with open(path, "rb") as f:
                image = Image.open(f).convert("RGB")
        except Exception:
            image = Image.new("RGB", (IMG_SIZE, IMG_SIZE))
        if self.transform is not None:
            image = self.transform(image)
        return image, label


train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(20),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


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


# ==================== 蒸馏损失 ====================


class DistillationLoss(nn.Module):
    """
    Loss = α · T² · KL( softmax(student/T) ‖ softmax(teacher/T) )
           + (1 - α) · CrossEntropy(student, label)
    """

    def __init__(self, temperature=4.0, alpha=0.7):
        super().__init__()
        assert 0.0 <= alpha <= 1.0, "alpha 必须在 [0, 1] 之间"
        self.temperature = temperature
        self.alpha = alpha
        self.kl_div = nn.KLDivLoss(reduction="batchmean")
        self.ce_loss = nn.CrossEntropyLoss()

    def forward(self, student_logits, teacher_logits, labels):
        # 两边都除以温度 T，得到软标签
        student_soft = F.log_softmax(student_logits / self.temperature, dim=1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=1)

        soft_loss = self.kl_div(student_soft, teacher_soft) * (self.temperature ** 2)
        hard_loss = self.ce_loss(student_logits, labels)

        total_loss = self.alpha * soft_loss + (1.0 - self.alpha) * hard_loss
        return total_loss, soft_loss, hard_loss


# ==================== 训练与评估 ====================


def train_one_epoch_distill(student, teacher, loader, criterion, optimizer, device, epoch):
    student.train()
    teacher.eval()

    running_loss = 0.0
    running_soft = 0.0
    running_hard = 0.0
    correct = 0
    total = 0

    progress = tqdm(loader, desc=f"Epoch {epoch}/{EPOCHS} [Distill]", ncols=100, leave=False)
    for images, labels in progress:
        images, labels = images.to(device), labels.to(device)

        # 教师只做推理，不更新梯度
        with torch.no_grad():
            teacher_logits = teacher(images)

        # 学生前向
        student_logits = student(images)
        loss, soft_loss, hard_loss = criterion(student_logits, teacher_logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        running_soft += soft_loss.item() * images.size(0)
        running_hard += hard_loss.item() * images.size(0)
        _, predicted = torch.max(student_logits, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        progress.set_postfix(
            loss=f"{running_loss / max(total, 1):.4f}",
            acc=f"{correct / max(total, 1):.4f}",
        )

    denom = max(total, 1)
    return running_loss / denom, running_soft / denom, running_hard / denom, correct / denom


def evaluate(model, loader, criterion, device, desc="Test"):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
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


def plot_history(history, save_path):
    try:
        epochs = range(1, len(history["train_loss"]) + 1)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

        axes[0].plot(epochs, history["train_acc"], "o-", label="学生训练准确率", color="#2E86DE")
        axes[0].plot(epochs, history["test_acc"], "s-", label="学生测试准确率", color="#EE5A24")
        axes[0].set_title("准确率曲线")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Accuracy")
        axes[0].grid(alpha=0.3)
        axes[0].legend()

        axes[1].plot(epochs, history["train_loss"], "o-", label="蒸馏总损失", color="#2E86DE")
        axes[1].plot(epochs, history["test_loss"], "s-", label="学生测试损失", color="#EE5A24")
        axes[1].set_title("损失曲线")
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("Loss")
        axes[1].grid(alpha=0.3)
        axes[1].legend()

        fig.suptitle("知识蒸馏训练曲线（教师 → 学生）", fontsize=14)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"蒸馏曲线已保存：{os.path.abspath(save_path)}")
    except Exception as exc:
        print(f"蒸馏曲线保存失败：{exc}")
        for i in range(len(history["train_loss"])):
            print(
                f"Epoch {i + 1:>3} | 蒸馏损失 {history['train_loss'][i]:.4f} | "
                f"训练准确率 {history['train_acc'][i]:.4f} | "
                f"测试损失 {history['test_loss'][i]:.4f} | "
                f"测试准确率 {history['test_acc'][i]:.4f}"
            )


# ==================== 主流程 ====================


def load_teacher(device):
    if not os.path.exists(TEACHER_PATH):
        print(f"未找到教师模型：{TEACHER_PATH}")
        print("请先运行：python 3.train_cnn.py")
        return None, None

    checkpoint = torch.load(TEACHER_PATH, map_location=device, weights_only=False)
    class_names = checkpoint.get("class_names")
    if not class_names:
        print("教师模型里没有 class_names，无法蒸馏。")
        return None, None

    teacher = DogCNN(num_classes=len(class_names))
    teacher.load_state_dict(checkpoint["model_state_dict"])
    teacher.to(device)
    teacher.eval()
    for param in teacher.parameters():
        param.requires_grad = False       # ★ 冻结教师，不参与反向传播

    return teacher, class_names


def main():
    set_seed(RANDOM_SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用计算设备：{device}")
    print(f"蒸馏配置：T={TEMPERATURE}，alpha={ALPHA}，epochs={EPOCHS}")

    teacher, class_names = load_teacher(device)
    if teacher is None:
        return

    print(f"\n类别顺序（{len(class_names)} 类）：")
    for idx, name in enumerate(class_names):
        print(f"  {idx} → {name}")

    # ---------- 扫描数据 ----------
    train_root = os.path.join(DATA_ROOT, "train")
    test_root = os.path.join(DATA_ROOT, "test")
    if not os.path.isdir(train_root) or not os.path.isdir(test_root):
        print("未找到划分后的数据集，请先运行：python 2.split_data.py")
        return

    dataset_classes = sorted(
        name for name in os.listdir(train_root)
        if os.path.isdir(os.path.join(train_root, name))
    )
    if dataset_classes != list(class_names):
        print("数据集类别与教师模型 class_names 不一致！")
        print(f"数据集：{dataset_classes}")
        print(f"教师模型：{class_names}")
        return

    class_to_idx = {name: idx for idx, name in enumerate(class_names)}

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
        print("训练集或测试集为空，无法蒸馏。")
        return

    train_dataset = DogDataset(train_samples, train_transform)
    test_dataset = DogDataset(test_samples, test_transform)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    # ---------- 教师基准 ----------
    ce_criterion = nn.CrossEntropyLoss()
    _, teacher_acc = evaluate(teacher, test_loader, ce_criterion, device, desc="Teacher")
    print(f"\n教师模型测试准确率：{teacher_acc:.4f} ({teacher_acc * 100:.2f}%)")

    # ---------- 学生初始化 ----------
    student = DogCNN(num_classes=len(class_names)).to(device)
    criterion = DistillationLoss(temperature=TEMPERATURE, alpha=ALPHA)
    optimizer = optim.Adam(student.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)

    history = {
        "train_loss": [], "train_acc": [],
        "test_loss": [], "test_acc": [],
        "soft_loss": [], "hard_loss": [],
    }
    best_acc = 0.0
    best_epoch = 0
    best_state = None

    print(f"\n开始蒸馏训练（{EPOCHS} epochs）...")
    start_time = time.time()

    for epoch in range(1, EPOCHS + 1):
        train_loss, soft_loss, hard_loss, train_acc = train_one_epoch_distill(
            student, teacher, train_loader, criterion, optimizer, device, epoch
        )
        test_loss, test_acc = evaluate(student, test_loader, ce_criterion, device, desc="Test")
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["test_loss"].append(test_loss)
        history["test_acc"].append(test_acc)
        history["soft_loss"].append(soft_loss)
        history["hard_loss"].append(hard_loss)

        if test_acc > best_acc:
            best_acc = test_acc
            best_epoch = epoch
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in student.state_dict().items()
            }

        print(f"Epoch {epoch} 总结：")
        print(f"  蒸馏总损失: {train_loss:.4f}（软 {soft_loss:.4f} + 硬 {hard_loss:.4f}）")
        print(f"  学生训练准确率: {train_acc:.4f}")
        print(f"  学生测试损失: {test_loss:.4f} | 学生测试准确率: {test_acc:.4f}")

    elapsed = time.time() - start_time
    last_acc = history["test_acc"][-1]

    if best_state is not None:
        student.load_state_dict(best_state)
    final_loss, final_acc = evaluate(student, test_loader, ce_criterion, device, desc="Best student")

    print("\n" + "=" * 60)
    print(f"教师模型测试准确率：{teacher_acc:.4f} ({teacher_acc * 100:.2f}%)")
    print(f"学生最后一轮准确率：{last_acc:.4f} ({last_acc * 100:.2f}%)")
    print(f"学生最佳准确率：{final_acc:.4f} ({final_acc * 100:.2f}%)，Epoch {best_epoch}")
    print(f"训练总耗时：{elapsed / 60:.1f} 分钟（{elapsed:.0f} 秒）")
    print("=" * 60)

    print_confusion_matrix(student, test_loader, device, class_names)

    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    torch.save({
        "model_state_dict": student.state_dict(),
        "class_names": class_names,
        "final_accuracy": final_acc,
        "best_test_acc": best_acc,
        "best_epoch": best_epoch,
        "last_test_acc": last_acc,
        "teacher_acc": teacher_acc,
        "temperature": TEMPERATURE,
        "alpha": ALPHA,
        "epochs": EPOCHS,
        "input_size": IMG_SIZE,
        "training_time_sec": elapsed,
        "history": history,
    }, STUDENT_PATH)
    print(f"学生模型已保存为：{os.path.abspath(STUDENT_PATH)}")

    plot_history(history, os.path.join(RESULTS_DIR, "distillation_history.png"))

    result_path = os.path.join(RESULTS_DIR, "distillation_result.txt")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("知识蒸馏结果\n")
        f.write("=" * 40 + "\n")
        f.write(f"类别数：{len(class_names)}\n")
        f.write(f"训练集/测试集：{len(train_samples)} / {len(test_samples)}\n")
        f.write(f"温度 T：{TEMPERATURE}\n")
        f.write(f"软损失权重 alpha：{ALPHA}\n")
        f.write(f"教师测试准确率：{teacher_acc:.4f} ({teacher_acc * 100:.2f}%)\n")
        f.write(f"学生最佳准确率：{final_acc:.4f} ({final_acc * 100:.2f}%)，Epoch {best_epoch}\n")
        f.write(f"训练总耗时：{elapsed / 60:.1f} 分钟\n")
    print(f"结果摘要已保存：{os.path.abspath(result_path)}")
    print("\n全部完成。学生模型可通过 4.classifier_ui.py --model models/distilled_dog_model.pth 加载。")


if __name__ == "__main__":
    main()