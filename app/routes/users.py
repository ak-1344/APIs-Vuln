from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import User

router = APIRouter()

# VULN: SQLi — raw string concatenation, no parameterization
@router.get("/users/search")
def search_users(name: str, db: Session = Depends(get_db)):
    raw_query = f"SELECT * FROM users WHERE email='{name}'"
    result = db.execute(text(raw_query))  # text() wrapper but STILL vulnerable
    return {"users": [dict(row) for row in result.mappings()]}

# VULN: returns all users with passwords — no auth
@router.get("/users/all")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()
