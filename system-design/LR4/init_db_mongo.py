import time
from pymongo import MongoClient
from passlib.context import CryptContext

# Настройка MongoDB
MONGO_URI = "mongodb://root:pass@mongo:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["carpooling"]
mongo_users_collection = mongo_db["users"]

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Загрузка тестовых данных
def load_test_data():
    # Проверка существования пользователя перед добавлением
    def add_user(username, first_name, last_name, hashed_password, email):
        user = mongo_users_collection.find_one({"username": username})
        if not user:
            user = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "hashed_password": hashed_password,
                "email": email,
            }
            mongo_users_collection.insert_one(user)

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

def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            mongo_client.admin.command('ismaster')
            print("Database is ready!")
            return
        except Exception as e:
            print(f"Database not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to the database")

if __name__ == "__main__":
    wait_for_db()
    load_test_data()