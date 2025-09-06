import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from blablacar_jwt import Base, RouteDB, TripDB

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/carpooling"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Загрузка тестовых данных
def load_test_data():
    db = SessionLocal()

    # Проверка существования маршрута перед добавлением
    def add_route(user_id, start_point, end_point):
        route = db.query(RouteDB).filter(RouteDB.user_id == user_id, RouteDB.start_point == start_point, RouteDB.end_point == end_point).first()
        if not route:
            route = RouteDB(
                user_id=user_id,
                start_point=start_point,
                end_point=end_point,
            )
            db.add(route)

    # Проверка существования поездки перед добавлением
    def add_trip(route_id, driver_id, passengers, date):
        trip = db.query(TripDB).filter(TripDB.route_id == route_id, TripDB.driver_id == driver_id, TripDB.date == date).first()
        if not trip:
            trip = TripDB(
                route_id=route_id,
                driver_id=driver_id,
                passengers=passengers,
                date=date,
            )
            db.add(trip)

    # Создание тестовых маршрутов
    add_route(user_id=1, start_point="Moscow", end_point="St. Petersburg")
    add_route(user_id=2, start_point="Moscow", end_point="Kazan")

    # Создание тестовых поездок
    add_trip(route_id=1, driver_id=1, passengers=[2], date="2023-10-01T10:00:00")
    add_trip(route_id=2, driver_id=2, passengers=[1], date="2023-10-02T12:00:00")

    db.commit()
    db.close()

def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            engine.connect()
            print("PostgreSQL is ready!")
            return
        except Exception as e:
            print(f"PostgreSQL not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to PostgreSQL")

if __name__ == "__main__":
    wait_for_db()
    load_test_data()