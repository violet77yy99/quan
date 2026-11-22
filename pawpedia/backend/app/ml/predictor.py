"""犬类品种推理：加载已经训练好的 8 类 DogCNN，只做推理，不训练。"""

import threading
from typing import Optional

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

from ..config import MODEL_PATH


class DogCNN(nn.Module):
    """与训练脚本保持一致的 4 层 CNN。"""

    def __init__(self, num_classes: int = 8):
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


class DogPredictor:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"未找到模型文件：{self.model_path}\n"
                "请把训练好的 dog_classification_model.pth 放到 backend/models/ 下。"
            )

        checkpoint = torch.load(
            self.model_path, map_location=self.device, weights_only=False
        )
        self.class_names = checkpoint.get("class_names") or [
            "中华田园犬", "柯基", "橘猫", "比格", "泰迪", "萨摩耶", "边牧", "金毛"
        ]
        self.final_accuracy = float(checkpoint.get("final_accuracy", 0.0))

        self.model = DogCNN(num_classes=len(self.class_names))
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose(
            [
                transforms.Resize((128, 128)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def predict(self, image: Image.Image) -> dict:
        image = image.convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        k = min(3, len(self.class_names))
        top_probs, top_indices = torch.topk(probs, k)
        top3 = [
            {
                "name_cn": self.class_names[int(idx)],
                "confidence": round(float(prob), 4),
            }
            for prob, idx in zip(top_probs.tolist(), top_indices.tolist())
        ]

        return {
            "name_cn": top3[0]["name_cn"],
            "confidence": top3[0]["confidence"],
            "top3": top3,
        }

    def info(self) -> dict:
        return {
            "model": "DogCNN",
            "classes": self.class_names,
            "num_classes": len(self.class_names),
            "final_accuracy": self.final_accuracy,
            "device": str(self.device),
        }


_predictor: Optional[DogPredictor] = None
_lock = threading.Lock()


def get_predictor() -> DogPredictor:
    """懒加载，第一次识别时再加载模型。"""
    global _predictor
    if _predictor is None:
        with _lock:
            if _predictor is None:
                _predictor = DogPredictor()
    return _predictor