"""数据库表：用户、犬种科普、识别记录。"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), default="")
    role = Column(String(20), default="user", index=True)  # user / admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    records = relationship(
        "RecognitionRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(80), unique=True, index=True, nullable=False)
    name_cn = Column(String(50), unique=True, index=True, nullable=False)
    name_en = Column(String(100), default="")
    intro = Column(Text, default="")
    personality = Column(String(255), default="")
    size_category = Column(String(20), default="中型犬", index=True)  # 小型犬/中型犬/大型犬/其他
    difficulty = Column(String(20), default="中等")
    origin = Column(String(100), default="")
    market_price = Column(String(100), default="")
    image_url = Column(String(255), default="")
    is_dog = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecognitionRecord(Base):
    __tablename__ = "recognition_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    image_url = Column(String(255), nullable=False)
    predicted_name = Column(String(50), index=True, nullable=False)
    confidence = Column(Float, default=0.0)
    top3 = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="records")