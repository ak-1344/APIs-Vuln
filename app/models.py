from app.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="user")
    credit = Column(Float, default=0.0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    product = Column(String)
    price = Column(Float)

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    vin = Column(String)
    location = Column(String, default="28.6139,77.2090")
