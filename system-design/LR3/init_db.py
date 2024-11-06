import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from blablacar_jwt import Base, UserDB, RouteDB, TripDB
from passlib.context import CryptContext

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/carpooling"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создание таблиц
Base.metadata.create_all(bind=engine)


# Загрузка тестовых данных
def load_test_data():
    db = SessionLocal()

    # Проверка существования пользователя перед добавлением
    def add_user(username, first_name, last_name, hashed_password, email):
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            user = UserDB(
                username=username,
                first_name=first_name,
                last_name=last_name,
                hashed_password=hashed_password,
                email=email,
            )
            db.add(user)


# Загрузка тестовых данных
def load_test_data():
    db = SessionLocal()

    # Создание мастер-пользователя
    master_user = UserDB(
        username="admin",
        first_name="Admin",
        last_name="Admin",
        hashed_password=pwd_context.hash("secret"),
        email="admin@example.com",
    )
    db.add(master_user)

    # Создание тестовых пользователей
    user1 = UserDB(
        username="user1",
        first_name="Ivan",
        last_name="Ivanov",
        hashed_password=pwd_context.hash("password1"),
        email="ivan.ivanov@example.com",
    )
    db.add(user1)

    user2 = UserDB(
        username="user2",
        first_name="Anna",
        last_name="Petrova",
        hashed_password=pwd_context.hash("password2"),
        email="anna.petrova@example.com",
    )
    db.add(user2)

    # Создание тестовых маршрутов
    route1 = RouteDB(user_id=user1.id, start_point="Moscow", end_point="Kazan")
    db.add(route1)

    route2 = RouteDB(user_id=user2.id, start_point="Kazan", end_point="Ufa")
    db.add(route2)

    # Создание тестовых поездок
    trip1 = TripDB(
        route_id=route1.id, driver_id=user1.id, passengers=[user2.id], date="2024-10-01T10:00:00"
    )
    db.add(trip1)

    trip2 = TripDB(
        route_id=route2.id, driver_id=user2.id, passengers=[user1.id], date="2024-10-02T10:00:00"
    )
    db.add(trip2)

    db.commit()
    db.close()


def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            engine.connect()
            print("Database is ready!")
            return
        except Exception as e:
            print(f"Database not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to the database")


if __name__ == "__main__":
    load_test_data()
