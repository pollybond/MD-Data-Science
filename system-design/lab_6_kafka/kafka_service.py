from confluent_kafka import Producer, Consumer, KafkaError
import json
from sqlalchemy.orm import Session
from models import RouteDB
from dependencies import SessionLocal
from settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
import redis

# Настройка Redis
redis_client = redis.from_url("redis://cache:6379/0", decode_responses=True)

# Kafka Producer
def get_kafka_producer():
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

# Kafka Consumer
def kafka_consumer_service():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "route-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([KAFKA_TOPIC])

    while True:
        msg = consumer.poll(1.0)  # Ожидание сообщений с таймаутом 1 секунда
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Ошибка Kafka: {msg.error()}")
                break

        # Обработка сообщения
        route_data = json.loads(msg.value().decode("utf-8"))
        db = SessionLocal()
        try:
            db_route = RouteDB(**route_data)
            db.add(db_route)
            db.commit()
            db.refresh(db_route)

            # Обновление кеша
            cache_key = f"routes:user_id:{route_data['user_id']}"
            routes = db.query(RouteDB).filter(RouteDB.user_id == route_data['user_id']).all()
            redis_client.set(cache_key, json.dumps([route.dict() for route in routes]))
        finally:
            db.close()

    consumer.close()