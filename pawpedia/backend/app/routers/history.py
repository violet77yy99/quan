"""用户识别历史。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import RecognitionRecord, User
from ..schemas import Message, RecordOut

router = APIRouter(prefix="/api/history", tags=["历史记录"])


@router.get("", response_model=list[RecordOut], summary="我的识别历史")
def my_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    records = (
        db.query(RecognitionRecord)
        .filter(RecognitionRecord.user_id == user.id)
        .order_by(RecognitionRecord.created_at.desc())
        .limit(100)
        .all()
    )
    return records


@router.delete("/{record_id}", response_model=Message, summary="删除一条历史")
def delete_history(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.get(RecognitionRecord, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(record)
    db.commit()
    return Message(message="已删除")