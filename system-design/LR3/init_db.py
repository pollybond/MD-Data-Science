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

    # Создание мастер-пользователя
    add_user(
        username="admin",
        first_name="Admin",
        last_name="Admin",
        hashed_password=pwd_context.hash("secret"),
        email="admin@example.com",
    )

    # Создание тестовых пользователей
    add_user(
        username="user1",
        first_name="Ivan",
        last_name="Ivanov",
        hashed_password=pwd_context.hash("password1"),
        email="ivan.ivanov@example.com",
    )

    add_user(
        username="user2",
        first_name="Anna",
        last_name="Petrova",
        hashed_password=pwd_context.hash("password2"),
        email="anna.petrova@example.com",
    )

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
