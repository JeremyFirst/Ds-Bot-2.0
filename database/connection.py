"""
Модуль для подключения к MySQL базе данных.
"""

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

load_dotenv()

# Параметры подключения к БД
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'admin_log_db')

# Обработка случая, когда порт уже указан в DB_HOST
if ':' in DB_HOST:
    # Если порт уже в хосте, извлекаем его
    host_parts = DB_HOST.rsplit(':', 1)
    DB_HOST = host_parts[0]
    if len(host_parts) > 1:
        DB_PORT = host_parts[1]

# Преобразуем порт в int для проверки
try:
    DB_PORT = int(DB_PORT)
except ValueError:
    DB_PORT = 3306

# URL-кодирование параметров для безопасной передачи специальных символов
encoded_user = quote_plus(DB_USER) if DB_USER else ''
encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ''
encoded_host = quote_plus(DB_HOST) if DB_HOST else 'localhost'
encoded_db = quote_plus(DB_NAME) if DB_NAME else 'admin_log_db'

# Строка подключения
DATABASE_URL = f"mysql+pymysql://{encoded_user}:{encoded_password}@{encoded_host}:{DB_PORT}/{encoded_db}?charset=utf8mb4"

# Создание движка
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Фабрика сессий
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db_session():
    """
    Получить сессию базы данных.
    
    Returns:
        Session: SQLAlchemy сессия
    """
    return SessionLocal()


def init_database():
    """
    Инициализировать базу данных (создать таблицы).
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)

