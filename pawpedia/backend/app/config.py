"""项目配置：路径、数据库、鉴权、上传限制等。"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
load_dotenv(BASE_DIR / ".env")

# 本地演示默认用 SQLite；部署时在 .env 里换成 MySQL：
# mysql+pymysql://pawpedia:pawpedia123@127.0.0.1:3306/pawpedia?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pawpedia.db")
if DATABASE_URL.startswith("sqlite:///./"):
    # 让 SQLite 文件固定落在 backend/ 下，不受启动目录影响
    DATABASE_URL = "sqlite:///" + (BASE_DIR / DATABASE_URL.replace("sqlite:///./", "")).as_posix()

SECRET_KEY = os.getenv("SECRET_KEY", "pawpedia-dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

CORS_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if item.strip()
]

UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
MODEL_PATH = Path(
    os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "dog_classification_model.pth"))
)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)