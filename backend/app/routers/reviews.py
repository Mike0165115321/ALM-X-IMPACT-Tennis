from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/matches", tags=["User Reviews (UGC)"])

# ----------------- Pydantic Request Models -----------------

class CreateReviewRequest(BaseModel):
    reviewee_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str

# ----------------- Route Endpoints -----------------

@router.post("/{id}/reviews", status_code=status.HTTP_201_CREATED)
async def submit_review(
    id: str, 
    payload: CreateReviewRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 1. ตรวจสอบว่า Match มีอยู่จริงหรือไม่
    match_val = await DataService.get_match_by_id(id)
    if not match_val:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลแมตช์ที่ระบุในระบบ"
        )
        
    # 2. ป้องกันการรีวิวตัวเอง (Self-review)
    if payload.reviewee_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="คุณไม่สามารถส่งรีวิวหรือให้คะแนนดาวตัวเองได้"
        )
        
    # 3. ตรวจสอบว่าผู้ถูกรีวิว (Reviewee) และผู้รีวิว (Reviewer) มีส่วนร่วมใน Match หรือไม่
    host_id = match_val.get("host_user_id")
    invited_ids = match_val.get("invited_user_ids") or []
    
    # ดึงค่าทั้งหมดที่เป็นผู้เล่นในแมตช์นี้
    match_participants = [host_id] + list(invited_ids)
    
    if current_user["id"] not in match_participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์ส่งรีวิวในแมตช์นี้ เนื่องจากคุณไม่ได้เป็นผู้ร่วมเล่นในแมตช์นี้"
        )
        
    if payload.reviewee_id not in match_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ผู้เล่นที่คุณต้องการรีวิวไม่ได้เป็นผู้ร่วมเล่นในแมตช์นี้"
        )
        
    review = await DataService.create_review(
        reviewer_id=current_user["id"],
        match_id=id,
        reviewee_id=payload.reviewee_id,
        rating=payload.rating,
        comment=payload.comment
    )
    
    return {
        "status": "success",
        "message": "Review submitted successfully",
        "review_id": review["id"]
    }
