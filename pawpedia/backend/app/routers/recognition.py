"""图片识别接口：游客可用，登录后自动保存历史。"""

import io
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from ..config import MAX_UPLOAD_MB, UPLOAD_DIR
from ..database import get_db
from ..deps import get_current_user_optional
from ..models import Breed, RecognitionRecord, User
from ..schemas import BreedOut, PredictResponse, PredictionOut, TopItem
from ..ml.predictor import get_predictor

router = APIRouter(prefix="/api/recognition", tags=["图片识别"])


@router.get("/info", summary="模型信息（类别、准确率、设备）")
def model_info():
    try:
        return get_predictor().info()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/predict", response_model=PredictResponse, summary="上传图片并识别")
async def predict(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="图片为空")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"图片不能超过 {MAX_UPLOAD_MB}MB")

    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="无法解析这张图片")

    # 限制原图尺寸，避免上传巨大的图片
    image.thumbnail((1280, 1280))

    try:
        result = get_predictor().predict(image)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    filename = f"{uuid.uuid4().hex}.jpg"
    image.save(UPLOAD_DIR / filename, "JPEG", quality=88, optimize=True)
    image_url = f"/uploads/{filename}"

    breed = (
        db.query(Breed).filter(Breed.name_cn == result["name_cn"]).first()
    )

    record_id = None
    saved = False
    if user is not None:
        record = RecognitionRecord(
            user_id=user.id,
            image_url=image_url,
            predicted_name=result["name_cn"],
            confidence=result["confidence"],
            top3=result["top3"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id
        saved = True

    return PredictResponse(
        prediction=PredictionOut(
            name_cn=result["name_cn"],
            confidence=result["confidence"],
            top3=[TopItem(**item) for item in result["top3"]],
        ),
        breed=BreedOut.model_validate(breed) if breed else None,
        saved=saved,
        record_id=record_id,
    )