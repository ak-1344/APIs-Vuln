from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

router = APIRouter()

# VULN: Broken Access Control — no role check, anyone can hit this
@router.get("/admin/users")
def admin_get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# VULN: Mass Assignment — blindly updates whatever fields are passed
@router.put("/admin/user/{user_id}")
def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    db.query(User).filter(User.id == user_id).update(data)
    db.commit()
    return {"status": "updated"}
