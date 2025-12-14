"""
RCON клиент для выполнения команд на Rust-сервере.
"""

import os
import logging
from typing import Optional, Dict
from rcon import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RCONClient:
    """
    Клиент для выполнения RCON команд.
    """
    
    def __init__(self):
        """
        Инициализировать RCON клиент из переменных окружения.
        """
        self.host = os.getenv('RCON_HOST', 'localhost')
        self.port = int(os.getenv('RCON_PORT', 28016))
        self.password = os.getenv('RCON_PASSWORD')
        
        if not self.password:
            logger.warning("RCON_PASSWORD не установлен в .env")
    
    def execute(self, command: str, timeout: int = 10) -> Optional[str]:
        """
        Выполнить RCON команду.
        
        Args:
            command: Команда для выполнения
            timeout: Таймаут в секундах
            
        Returns:
            Ответ сервера или None при ошибке
        """
        try:
            with Client(self.host, self.port, passwd=self.password, timeout=timeout) as client:
                response = client.run(command)
                return response
        except Exception as e:
            logger.error(f"Ошибка RCON при выполнении команды '{command}': {e}")
            return None
    
    def get_player_info(self, steam_id: str, timeout: int = 10, retry_attempts: int = 3) -> Optional[str]:
        """
        Получить информацию об игроке через pinfo.
        
        Args:
            steam_id: SteamID игрока
            timeout: Таймаут в секундах
            retry_attempts: Количество попыток при ошибке
            
        Returns:
            Ответ команды pinfo или None при ошибке
        """
        command = f"pinfo {steam_id}"
        
        for attempt in range(retry_attempts):
            response = self.execute(command, timeout)
            if response is not None:
                return response
            
            if attempt < retry_attempts - 1:
                logger.warning(f"Попытка {attempt + 1}/{retry_attempts} не удалась, повтор...")
        
        return None

