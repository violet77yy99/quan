"""Pydantic 请求/响应模型。"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- 用户 / 鉴权 ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: Optional[str] = ""
    role: str
    is_active: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=64)
    nickname: Optional[str] = Field(default="", max_length=30)


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(user|admin)$")
    is_active: Optional[bool] = None


# ---------- 犬种科普 ----------

class BreedBase(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    name_cn: str = Field(min_length=1, max_length=50)
    name_en: str = ""
    intro: str = ""
    personality: str = ""
    size_category: str = "中型犬"
    difficulty: str = "中等"
    origin: str = ""
    market_price: str = ""
    image_url: str = ""
    is_dog: bool = True


class BreedCreate(BreedBase):
    pass


class BreedUpdate(BaseModel):
    slug: Optional[str] = None
    name_cn: Optional[str] = None
    name_en: Optional[str] = None
    intro: Optional[str] = None
    personality: Optional[str] = None
    size_category: Optional[str] = None
    difficulty: Optional[str] = None
    origin: Optional[str] = None
    market_price: Optional[str] = None
    image_url: Optional[str] = None
    is_dog: Optional[bool] = None


class BreedOut(BreedBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ---------- 识别 ----------

class TopItem(BaseModel):
    name_cn: str
    confidence: float


class PredictionOut(BaseModel):
    name_cn: str
    confidence: float
    top3: List[TopItem]


class PredictResponse(BaseModel):
    prediction: PredictionOut
    breed: Optional[BreedOut] = None
    saved: bool = False
    record_id: Optional[int] = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    predicted_name: str
    confidence: float
    top3: Optional[List[TopItem]] = None
    created_at: datetime


class AdminRecordOut(RecordOut):
    username: Optional[str] = None
    nickname: Optional[str] = None


class AdminOverview(BaseModel):
    total_users: int
    total_records: int
    total_breeds: int
    today_records: int
    recent_records: List[AdminRecordOut]
    top_breeds: List[dict]


class Message(BaseModel):
    message: str