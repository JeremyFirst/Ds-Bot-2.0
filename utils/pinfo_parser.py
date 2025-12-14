"""
Парсер ответа команды pinfo из Rust-сервера.
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def parse_pinfo_response(response: str, privilege_groups: list) -> Optional[Dict[str, Any]]:
    """
    Парсить ответ команды pinfo.
    
    Ожидаемый формат ответа (пример):
    Player "PlayerName" (SteamID) - Group: admin, Expires: 2024-12-31 23:59:59
    
    Или если привилегии нет:
    Player "PlayerName" (SteamID) - No privileges
    
    Args:
        response: Ответ команды pinfo
        privilege_groups: Список групп привилегий из config.yml
        
    Returns:
        Dict с ключами:
            - has_privilege: bool
            - group: str или None
            - expires_at: datetime или None
        Или None если формат не распознан
    """
    if not response or not isinstance(response, str):
        return None
    
    response = response.strip()
    
    # Проверяем, есть ли привилегия
    if "No privileges" in response or "no privileges" in response.lower():
        return {
            'has_privilege': False,
            'group': None,
            'expires_at': None
        }
    
    # Ищем группу привилегии
    group = None
    for priv_group in privilege_groups:
        # Ищем паттерн "Group: groupname" или "group: groupname"
        pattern = rf'(?:Group|group):\s*{re.escape(priv_group)}'
        if re.search(pattern, response, re.IGNORECASE):
            group = priv_group
            break
    
    # Ищем дату окончания
    expires_at = None
    # Паттерны для даты: "Expires: 2024-12-31 23:59:59" или "expires: 2024-12-31 23:59:59"
    expire_patterns = [
        r'(?:Expires|expires):\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        r'(?:Expires|expires):\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})',
    ]
    
    for pattern in expire_patterns:
        match = re.search(pattern, response)
        if match:
            date_str = match.group(1)
            try:
                # Пробуем разные форматы
                for fmt in ["%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"]:
                    try:
                        expires_at = datetime.strptime(date_str, fmt)
                        # Считаем что время в UTC
                        expires_at = expires_at.replace(tzinfo=None)  # Будет храниться как UTC без timezone
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Не удалось распарсить дату '{date_str}': {e}")
    
    # Если группа найдена, значит привилегия есть
    has_privilege = group is not None
    
    return {
        'has_privilege': has_privilege,
        'group': group,
        'expires_at': expires_at
    }

