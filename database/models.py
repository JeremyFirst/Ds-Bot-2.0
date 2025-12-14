"""
Модели базы данных для Discord-бота.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StaffMessage(Base):
    """
    Модель для хранения информации о сообщении /staff.
    """
    __tablename__ = 'staff_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, nullable=False, unique=True)
    message_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserPrivilege(Base):
    """
    Модель для хранения привилегий пользователей.
    """
    __tablename__ = 'user_privileges'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_user_id = Column(BigInteger, nullable=False, index=True)
    steam_id = Column(String(17), nullable=False, unique=True, index=True)
    privilege_group = Column(String(100), nullable=True)  # Название группы из Oxide
    expires_at = Column(DateTime, nullable=True)  # UTC время окончания привилегии
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserPrivilege(discord_id={self.discord_user_id}, steam_id={self.steam_id}, group={self.privilege_group})>"

