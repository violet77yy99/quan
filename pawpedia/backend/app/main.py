"""汪星图鉴 · 犬类品种识别与科普系统 —— FastAPI 入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, STATIC_DIR, UPLOAD_DIR
from .database import Base, SessionLocal, engine
from .routers import admin, auth, breeds, history, recognition
from .seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 自动建表 + 初始化默认账号和科普数据
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)
    yield


app = FastAPI(
    title="汪星图鉴 · 犬类品种识别与科普系统 API",
    description=(
        "前后端分离的犬类识别与科普系统。\n\n"
        "- 游客：浏览图鉴、直接识别（不保存记录）\n"
        "- 用户：登录后识别并保存历史\n"
        "- 管理员：数据概览、用户管理、识别记录、科普内容编辑\n\n"
        "默认账号：admin / admin123，user / user123456"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(breeds.router)
app.include_router(recognition.router)
app.include_router(history.router)
app.include_router(admin.router)


@app.get("/", tags=["系统"], summary="欢迎页")
def root():
    return {
        "name": "汪星图鉴 · 犬类品种识别与科普系统",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok"}