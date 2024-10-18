from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Псевдо-база данных пользователей
client_db = {
    "admin": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # hashed "secret"
}

# Временное хранилище для пользователей, маршрутов и поездок
users_db = []
routes_db = []
trips_db = []


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
    password_check = False
    if form_data.username in client_db:
        password = client_db[form_data.username]
        if pwd_context.verify(form_data.password, password):
            password_check = True

    if password_check:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
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
    for u in users_db:
        if u.id == user.id:
            raise HTTPException(status_code=404, detail="User already exists")
    users_db.append(user)
    return user


# Поиск пользователя по логину
@app.get("/users/{username}", response_model=User)
def get_user_by_username(username: str, current_user: str = Depends(get_current_client)):
    for user in users_db:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")


# Поиск пользователя по маске имени и фамилии
@app.get("/users", response_model=List[User])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    matching_users = [
        user
        for user in users_db
        if first_name.lower() in user.first_name.lower()
        and last_name.lower() in user.last_name.lower()
    ]
    return matching_users


# Создание маршрута
@app.post("/routes", response_model=Route)
def create_route(route: Route, current_user: str = Depends(get_current_client)):
    for r in routes_db:
        if r.id == route.id:
            raise HTTPException(status_code=404, detail="Route already exists")
    routes_db.append(route)
    return route


# Получение маршрутов пользователя
@app.get("/routes", response_model=List[Route])
def get_user_routes(user_id: int, current_user: str = Depends(get_current_client)):
    user_routes = [route for route in routes_db if route.user_id == user_id]
    return user_routes


# Создание поездки
@app.post("/trips", response_model=Trip)
def create_trip(trip: Trip, current_user: str = Depends(get_current_client)):
    for t in trips_db:
        if t.id == trip.id:
            raise HTTPException(status_code=404, detail="Trip already exists")
    trips_db.append(trip)
    return trip


# Подключение пользователей к поездке
@app.post("/trips/{trip_id}/join", response_model=Trip)
def join_trip(trip_id: int, user_id: int, current_user: str = Depends(get_current_client)):
    for trip in trips_db:
        if trip.id == trip_id:
            if user_id not in trip.passengers:
                trip.passengers.append(user_id)
            return trip
    raise HTTPException(status_code=404, detail="Trip not found")


# Получение информации о поездке
@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip_info(trip_id: int, current_user: str = Depends(get_current_client)):
    for trip in trips_db:
        if trip.id == trip_id:
            return trip
    raise HTTPException(status_code=404, detail="Trip not found")

# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

# Запуск сервера
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
