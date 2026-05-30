from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/store", tags=["Storefront & Equipment Rental (Phase 3)"])

class OrderItemSchema(BaseModel):
    item_id: str
    quantity: int

class OrderCreateRequest(BaseModel):
    items: List[OrderItemSchema]
    court_booking_id: Optional[str] = None

@router.get("/items", response_model=List[Dict[str, Any]])
async def list_store_items(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    ดึงรายการสินค้า น้ำดื่ม ลูกเทนนิส และไม้เทนนิสเช่าที่มีให้บริการในระบบ
    """
    return await DataService.get_store_items()

@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_store_order(payload: OrderCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    สร้างรายการสั่งซื้อน้ำดื่ม ลูกเทนนิส หรือทำรายการเช่าอุปกรณ์
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="กรุณาเลือกสินค้าอย่างน้อย 1 รายการเพื่อทำรายการสั่งซื้อ"
        )
        
    items_list = [{"item_id": i.item_id, "quantity": i.quantity} for i in payload.items]
    
    try:
        order = await DataService.create_order(
            user_id=current_user["id"],
            items=items_list,
            court_booking_id=payload.court_booking_id
        )
        return {
            "message": "Order created successfully",
            "order_id": order["id"],
            "total_price": order["total_price"],
            "status": order["status"]
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"เกิดข้อผิดพลาดในการสร้างคำสั่งซื้อ: {str(e)}"
        )

@router.get("/orders", response_model=List[Dict[str, Any]])
async def list_user_orders(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    ดึงรายการประวัติการสั่งซื้อและประวัติเช่าสินค้าทั้งหมดของผู้ใช้งานแต่ละราย
    (หากเป็น admin จะดึงรายการทั้งหมดในระบบ)
    """
    if current_user["role"] == "admin":
        return await DataService.get_all_orders()
    return await DataService.get_orders_by_user(current_user["id"])
