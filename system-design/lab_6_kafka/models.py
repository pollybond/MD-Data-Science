from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserMongo(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    hashed_password: str
    email: str

class Route(BaseModel):
    id: int
    user_id: int
    start_point: str
    end_point: str

class Trip(BaseModel):
    id: int
    route_id: int
    driver_id: int
    passengers: List[int] = []
    date: datetime

class RouteDB(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    start_point = Column(String, index=True)
    end_point = Column(String, index=True)

class TripDB(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, index=True)
    driver_id = Column(Integer, index=True)
    passengers = Column(String, index=True)
    date = Column(DateTime, index=True)