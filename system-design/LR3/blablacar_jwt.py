from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, ARRAY, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/carpooling"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
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


# Модели данных
class User(BaseModel):
    id: int
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
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)


class RouteDB(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_point = Column(String)
    end_point = Column(String)


class TripDB(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    driver_id = Column(Integer, ForeignKey("users.id"))
    passengers = Column(ARRAY(Integer), default=[])
    date = Column(DateTime)


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
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    db.close()

    if user and pwd_context.verify(form_data.password, user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Создание нового пользователя
@app.post("/users", response_model=User)
def create_user(user: User, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    db_user = UserDB(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return user


# Поиск пользователя по логину
@app.get("/users/{username}", response_model=User)
def get_user_by_username(username: str, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == username).first()
    db.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Поиск пользователя по маске имени и фамилии
@app.get("/users", response_model=List[User])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    db = SessionLocal()
    users = (
        db.query(UserDB)
        .filter(
            UserDB.first_name.ilike(f"%{first_name}%"), UserDB.last_name.ilike(f"%{last_name}%")
        )
        .all()
    )
    db.close()
    return users


# Создание маршрута
@app.post("/routes", response_model=Route)
def create_route(route: Route, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    db_route = RouteDB(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    db.close()
    return route


# Получение маршрутов пользователя
@app.get("/routes", response_model=List[Route])
def get_user_routes(user_id: int, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    routes = db.query(RouteDB).filter(RouteDB.user_id == user_id).all()
    db.close()
    return routes


# Создание поездки
@app.post("/trips", response_model=Trip)
def create_trip(trip: Trip, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    db_trip = TripDB(**trip.dict())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    db.close()
    return trip


# Подключение пользователей к поездке
@app.post("/trips/{trip_id}/join", response_model=Trip)
def join_trip(trip_id: int, user_id: int, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    if trip:
        if user_id not in trip.passengers:
            trip.passengers.append(user_id)
            db.commit()
            db.refresh(trip)
        db.close()
        return trip
    db.close()
    raise HTTPException(status_code=404, detail="Trip not found")


# Получение информации о поездке
@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip_info(trip_id: int, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    db.close()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
