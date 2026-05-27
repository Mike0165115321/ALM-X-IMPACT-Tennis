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
def submit_review(
    id: str, 
    payload: CreateReviewRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    review = DataService.create_review(
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
