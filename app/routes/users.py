from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

router = APIRouter()

# VULN: SQLi — f-string query, no parameterization
@router.get("/users/search")
def search_users(name: str, db: Session = Depends(get_db)):
    result = db.execute(f"SELECT * FROM users WHERE email='{name}'")
    return {"users": [dict(row) for row in result.mappings()]}

# VULN: returns all users with passwords — no auth
@router.get("/users/all")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()
