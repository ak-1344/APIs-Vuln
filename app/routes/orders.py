from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order
from typing import Optional

router = APIRouter()

# VULN: BOLA — fetches any order by ID, no ownership check
@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db),
              user_id: Optional[int] = Header(None)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": "not found"}
    return order

@router.get("/orders/my/all")
def my_orders(user_id: int, db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user_id).all()
