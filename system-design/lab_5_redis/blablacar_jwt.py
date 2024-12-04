from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pymongo import MongoClient
from bson import ObjectId
import redis
import os
import json 


# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/carpooling"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Настройка Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Подключение к MongoDB
MONGO_URI = "mongodb://root:pass@mongo:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["carpooling"]
mongo_users_collection = mongo_db["users"]

# Модели данных
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

# SQLAlchemy models
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

# Зависимости для получения текущего пользователя
async def get_current_client(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        else:
            return username
    except JWTError:
        raise credentials_exception

# Создание и проверка JWT токенов
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Маршрут для получения токена
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = mongo_users_collection.find_one({"username": form_data.username})

    if user and pwd_context.verify(form_data.password, user["hashed_password"]):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Создание нового пользователя
@app.post("/users", response_model=UserMongo)
def create_user(user: UserMongo, current_user: str = Depends(get_current_client)):
    user_dict = user.dict()
    user_dict["hashed_password"] = pwd_context.hash(user_dict["hashed_password"])
    user_id = mongo_users_collection.insert_one(user_dict).inserted_id
    user_dict["id"] = str(user_id)
    return user_dict

# Поиск пользователя по логину
@app.get("/users/{username}", response_model=UserMongo)
def get_user_by_username(username: str, current_user: str = Depends(get_current_client)):
    user = mongo_users_collection.find_one({"username": username})
    if user:
        user["id"] = str(user["_id"])
        return user
    raise HTTPException(status_code=404, detail="User not found")

# Поиск пользователя по маске имени и фамилии
@app.get("/users", response_model=List[UserMongo])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    users = list(mongo_users_collection.find({"first_name": {"$regex": first_name, "$options": "i"}, "last_name": {"$regex": last_name, "$options": "i"}}))
    for user in users:
        user["id"] = str(user["_id"])
    return users

# Зависимости для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание маршрута
@app.post("/routes", response_model=Route)
def create_route(route: Route, db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    db_route = RouteDB(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)

    # Обновление кеша
    cache_key = f"routes:user_id:{route.user_id}"
    routes = db.query(RouteDB).filter(RouteDB.user_id == route.user_id).all()
    redis_client.set(cache_key, json.dumps([route.dict() for route in routes]))

    return route

# Получение маршрутов пользователя
@app.get("/routes", response_model=List[Route])
def get_user_routes(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    cache_key = f"routes:user_id:{user_id}"
    cached_routes = redis_client.get(cache_key)

    if cached_routes:
        return [Route(**route) for route in json.loads(cached_routes)]

    routes = db.query(RouteDB).filter(RouteDB.user_id == user_id).all()
    if routes:
        redis_client.set(cache_key, json.dumps([route.dict() for route in routes]))

    return routes

# Создание поездки
@app.post("/trips", response_model=Trip)
def create_trip(trip: Trip, db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    db_trip = TripDB(**trip.dict())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return trip

# Подключение пользователей к поездке
@app.post("/trips/{trip_id}/join", response_model=Trip)
def join_trip(trip_id: int, user_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    if trip:
        if user_id not in trip.passengers:
            trip.passengers.append(user_id)
            db.commit()
            db.refresh(trip)
        return trip
    raise HTTPException(status_code=404, detail="Trip not found")

# Получение информации о поездке
@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip_info(trip_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip



# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)