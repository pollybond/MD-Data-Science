import os

# Kafka
KAFKA_BOOTSTRAP_SERVERS = "kafka1:9092"
KAFKA_TOPIC = "routes"

# JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB
MONGO_URI = "mongodb://root:pass@mongo:27017/"

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")

# PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/carpooling"