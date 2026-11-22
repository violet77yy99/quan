"""管理端接口：数据概览、用户、识别记录、科普内容 CRUD。"""

from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Breed, RecognitionRecord, User
from ..schemas import (
    AdminOverview,
    AdminRecordOut,
    BreedCreate,
    BreedOut,
    BreedUpdate,
    Message,
    UserOut,
    UserUpdate,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["管理端"],
    dependencies=[Depends(require_admin)],
)


def _record_with_user(record: RecognitionRecord, user: User | None) -> AdminRecordOut:
    data = AdminRecordOut.model_validate(record).model_dump()
    data["username"] = user.username if user else None
    data["nickname"] = user.nickname if user else None
    return AdminRecordOut(**data)


@router.get("/overview", response_model=AdminOverview, summary="数据概览")
def overview(db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_records = db.query(func.count(RecognitionRecord.id)).scalar() or 0
    total_breeds = db.query(func.count(Breed.id)).scalar() or 0

    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_records = (
        db.query(func.count(RecognitionRecord.id))
        .filter(RecognitionRecord.created_at >= today_start)
        .scalar()
        or 0
    )

    recent_rows = (
        db.query(RecognitionRecord, User)
        .outerjoin(User, RecognitionRecord.user_id == User.id)
        .order_by(RecognitionRecord.created_at.desc())
        .limit(5)
        .all()
    )
    recent_records = [_record_with_user(rec, user) for rec, user in recent_rows]

    top_rows = (
        db.query(
            RecognitionRecord.predicted_name,
            func.count(RecognitionRecord.id).label("cnt"),
        )
        .group_by(RecognitionRecord.predicted_name)
        .order_by(func.count(RecognitionRecord.id).desc())
        .limit(5)
        .all()
    )
    top_breeds = [{"name": name, "count": count} for name, count in top_rows]

    return AdminOverview(
        total_users=total_users,
        total_records=total_records,
        total_breeds=total_breeds,
        today_records=today_records,
        recent_records=recent_records,
        top_breeds=top_breeds,
    )


@router.get("/users", response_model=list[UserOut], summary="用户列表")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.asc()).all()


@router.patch("/users/{user_id}", response_model=UserOut, summary="修改用户角色/状态")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if target.id == admin.id:
        if data.is_active is False:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        if data.role is not None and data.role != "admin":
            raise HTTPException(status_code=400, detail="不能取消自己的管理员身份")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return target


@router.get("/records", response_model=list[AdminRecordOut], summary="全部识别记录")
def list_records(db: Session = Depends(get_db)):
    rows = (
        db.query(RecognitionRecord, User)
        .outerjoin(User, RecognitionRecord.user_id == User.id)
        .order_by(RecognitionRecord.created_at.desc())
        .limit(200)
        .all()
    )
    return [_record_with_user(rec, user) for rec, user in rows]


@router.delete("/records/{record_id}", response_model=Message, summary="删除识别记录")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(RecognitionRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return Message(message="已删除")


@router.post("/breeds", response_model=BreedOut, summary="新增科普内容")
def create_breed(data: BreedCreate, db: Session = Depends(get_db)):
    if db.query(Breed).filter(Breed.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="slug 已存在")
    if db.query(Breed).filter(Breed.name_cn == data.name_cn).first():
        raise HTTPException(status_code=400, detail="中文名已存在")

    payload = data.model_dump()
    if not payload.get("image_url"):
        payload["image_url"] = f"/static/breeds/{payload['slug']}.jpg"

    breed = Breed(**payload)
    db.add(breed)
    db.commit()
    db.refresh(breed)
    return breed


@router.put("/breeds/{breed_id}", response_model=BreedOut, summary="编辑科普内容")
def update_breed(breed_id: int, data: BreedUpdate, db: Session = Depends(get_db)):
    breed = db.get(Breed, breed_id)
    if breed is None:
        raise HTTPException(status_code=404, detail="科普内容不存在")

    payload = data.model_dump(exclude_unset=True)
    if "slug" in payload and payload["slug"] != breed.slug:
        if db.query(Breed).filter(Breed.slug == payload["slug"]).first():
            raise HTTPException(status_code=400, detail="slug 已存在")
    if "name_cn" in payload and payload["name_cn"] != breed.name_cn:
        if db.query(Breed).filter(Breed.name_cn == payload["name_cn"]).first():
            raise HTTPException(status_code=400, detail="中文名已存在")

    for key, value in payload.items():
        setattr(breed, key, value)

    db.commit()
    db.refresh(breed)
    return breed


@router.delete("/breeds/{breed_id}", response_model=Message, summary="删除科普内容")
def delete_breed(breed_id: int, db: Session = Depends(get_db)):
    breed = db.get(Breed, breed_id)
    if breed is None:
        raise HTTPException(status_code=404, detail="科普内容不存在")
    db.delete(breed)
    db.commit()
    return Message(message="已删除")