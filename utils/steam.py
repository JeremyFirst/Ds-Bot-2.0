"""
Утилиты для работы со SteamID.
"""

import re


def validate_steam_id(steam_id: str) -> bool:
    """
    Валидировать SteamID.
    
    SteamID может быть в форматах:
    - STEAM_0:0:12345678 (старый формат)
    - 76561198000000000 (64-bit формат)
    
    Args:
        steam_id: SteamID для валидации
        
    Returns:
        True если SteamID валиден, False иначе
    """
    if not steam_id or not isinstance(steam_id, str):
        return False
    
    steam_id = steam_id.strip()
    
    # Проверка старого формата STEAM_0:X:YYYYYYYY
    old_format = re.match(r'^STEAM_[0-5]:[01]:\d+$', steam_id)
    if old_format:
        return True
    
    # Проверка 64-bit формата (17 цифр, начинается с 7656119)
    if re.match(r'^7656119\d{10}$', steam_id):
        return True
    
    return False

