from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order
from typing import Optional

router = APIRouter()

def verify_ownership(order: Order, user_id: int):
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden — not your resource")

# FIXED: ownership check before returning order
@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db),
              user_id: Optional[int] = Header(None)):
    if not user_id:
        raise HTTPException(status_code=401, detail="user-id header required")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")
    verify_ownership(order, user_id)  # BOLA fix — ownership enforced
    return order

@router.get("/orders/my/all")
def my_orders(user_id: int, db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user_id).all()
