from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

def require_admin(requesting_user_id: Optional[int] = Header(None),
                  db: Session = Depends(get_db)):
    if not requesting_user_id:
        raise HTTPException(status_code=401, detail="requesting-user-id header required")
    user = db.query(User).filter(User.id == requesting_user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/admin/users")
def admin_get_all_users(db: Session = Depends(get_db),
                        admin=Depends(require_admin)):
    return db.query(User).all()

@router.put("/admin/user/{user_id}")
def update_user(user_id: int,
                data: UserUpdateSchema,
                db: Session = Depends(get_db),
                admin=Depends(require_admin)):
    update_data = data.dict(exclude_unset=True)
    if not update_data:
        return {"status": "nothing to update"}
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    return {"status": "updated", "fields_changed": list(update_data.keys())}
