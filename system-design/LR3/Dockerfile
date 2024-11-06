# Базовый образ Python
FROM python:3.9-slim

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов проекта
COPY . .

# Права на выполнение для init_db.sh
RUN chmod +x init_db.sh

# Запуск приложения
CMD ["sh", "-c", "/app/init_db.sh && python init_db.py && uvicorn blablacar_jwt:app --host 0.0.0.0 --port 8000"]
