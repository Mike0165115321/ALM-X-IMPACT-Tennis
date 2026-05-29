from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/matching", tags=["Matchmaking"])

# ----------------- Pydantic Request Models -----------------

class FindMatchRequest(BaseModel):
    court_id: str
    match_date: str
    time_slot: str
    match_type: str = "singles"
    ntrp_min: float
    ntrp_max: float
    preferred_playing_style: Optional[str] = None

# ----------------- Route Endpoints -----------------

@router.post("/find")
async def find_matching(payload: FindMatchRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_profile = current_user.get("profile") or {}
    
    # 0. Enforce phone verification guard
    if not user_profile.get("is_phone_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="คุณต้องทำการยืนยันตัวตนผ่านเบอร์โทรศัพท์ (OTP) ก่อนจึงจะสามารถใช้ระบบหาคู่เล่นได้"
        )
        
    # 1. ค้นหาผู้เล่นแมตช์ที่เข้าเกณฑ์ตามสไตล์ NTRP และความต้องการ
    compatible_players = await DataService.find_matches(
        court_id=payload.court_id,
        match_date=payload.match_date,
        time_slot=payload.time_slot,
        match_type=payload.match_type,
        ntrp_min=payload.ntrp_min,
        ntrp_max=payload.ntrp_max,
        preferred_playing_style=payload.preferred_playing_style
    )
    
    # 2. สร้าง/ประกาศโพสต์สำหรับแมตช์นี้ในระบบหาคู่เล่นเพื่อรอคนอื่นเข้ามาร่วม
    new_match = await DataService.create_match_post(
        host_user_id=current_user["id"],
        court_id=payload.court_id,
        match_date=payload.match_date,
        time_slot=payload.time_slot,
        match_type=payload.match_type,
        ntrp_min=payload.ntrp_min,
        ntrp_max=payload.ntrp_max
    )
    
    # ดึงรายชื่อผู้เล่นคนอื่นที่ไม่ใช่ host
    filtered_compatible = [p for p in compatible_players if p["user_id"] != current_user["id"]]
    
    return {
        "match_id": new_match["id"],
        "status": new_match["status"],
        "host": {
            "username": current_user["username"],
            "ntrp": user_profile.get("ntrp_rating", 1.5),
            "playing_style": user_profile.get("playing_style", "All-Court")
        },
        "compatible_matches": filtered_compatible
    }
