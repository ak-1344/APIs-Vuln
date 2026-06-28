from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

router = APIRouter()

# FIXED: ORM query — SQL never written as string
@router.get("/users/search")
def search_users(name: str, db: Session = Depends(get_db)):
    results = db.query(User).filter(User.email == name).all()
    return {"users": [{"id": u.id, "email": u.email, "role": u.role} for u in results]}

# FIXED: passwords removed from response
@router.get("/users/all")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "role": u.role} for u in users]
