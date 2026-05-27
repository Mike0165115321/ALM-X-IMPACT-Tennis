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
def find_matching(payload: FindMatchRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    # 1. ค้นหาผู้เล่นแมตช์ที่เข้าเกณฑ์ตามสไตล์ NTRP และความต้องการ
    compatible_players = DataService.find_matches(
        court_id=payload.court_id,
        match_date=payload.match_date,
        time_slot=payload.time_slot,
        match_type=payload.match_type,
        ntrp_min=payload.ntrp_min,
        ntrp_max=payload.ntrp_max,
        preferred_playing_style=payload.preferred_playing_style
    )
    
    # 2. สร้าง/ประกาศโพสต์สำหรับแมตช์นี้ในระบบหาคู่เล่นเพื่อรอคนอื่นเข้ามาร่วม
    new_match = DataService.create_match_post(
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
            "ntrp": current_user["profile"]["ntrp_rating"],
            "playing_style": current_user["profile"]["playing_style"]
        },
        "compatible_matches": filtered_compatible
    }
