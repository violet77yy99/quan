"""公开的犬种科普接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Breed
from ..schemas import BreedOut

router = APIRouter(prefix="/api/breeds", tags=["犬种科普"])


@router.get("", response_model=list[BreedOut], summary="犬种列表（搜索 + 体型筛选）")
def list_breeds(
    search: Optional[str] = Query(default=None, description="按中文名/英文名/简介搜索"),
    size: Optional[str] = Query(default=None, description="小型犬/中型犬/大型犬/其他"),
    db: Session = Depends(get_db),
):
    query = db.query(Breed)

    if search:
        keyword = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Breed.name_cn.ilike(keyword),
                Breed.name_en.ilike(keyword),
                Breed.intro.ilike(keyword),
            )
        )

    if size and size not in ("全部", "all"):
        query = query.filter(Breed.size_category == size)

    return query.order_by(Breed.id.asc()).all()


@router.get("/by-slug/{slug}", response_model=BreedOut, summary="按 slug 查询犬种")
def get_breed_by_slug(slug: str, db: Session = Depends(get_db)):
    breed = db.query(Breed).filter(Breed.slug == slug).first()
    if breed is None:
        raise HTTPException(status_code=404, detail="犬种不存在")
    return breed


@router.get("/{breed_id}", response_model=BreedOut, summary="按 ID 查询犬种")
def get_breed(breed_id: int, db: Session = Depends(get_db)):
    breed = db.get(Breed, breed_id)
    if breed is None:
        raise HTTPException(status_code=404, detail="犬种不存在")
    return breed