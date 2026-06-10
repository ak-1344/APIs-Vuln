from fastapi import FastAPI
from app.database import engine, Base
from app.routes import users, orders, admin, mechanic
from app.models import User, Order, Vehicle
from app.database import SessionLocal

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vulnerable API — Week 2")

app.include_router(users.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(mechanic.router)

@app.get("/")
def root():
    return {
        "message": "Vulnerable API is running",
        "docs": "/docs"
    }

# Seed test data on startup
@app.on_event("startup")
def seed():
    db = SessionLocal()
    if db.query(User).count() == 0:
        db.add_all([
            User(id=1, email="user_a@test.com", password="pass123", role="user", credit=100),
            User(id=2, email="user_b@test.com", password="pass456", role="user", credit=50),
            User(id=3, email="admin@test.com",  password="admin123", role="admin", credit=0),
        ])
        db.add_all([
            Order(id=1, user_id=1, product="Wheel", price=299.0),
            Order(id=2, user_id=2, product="Engine Oil", price=49.0),
            Order(id=3, user_id=1, product="Brake Pads", price=89.0),
        ])
        db.add_all([
            Vehicle(id=1, user_id=1, vin="VIN001AAA", location="28.6139,77.2090"),
            Vehicle(id=2, user_id=2, vin="VIN002BBB", location="19.0760,72.8777"),
        ])
        db.commit()
    db.close()
