"""
Модуль для загрузки конфигурации из config.yml.
"""

import yaml
import os
from typing import Dict, Any, Optional

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: str = 'config.yml') -> Dict[str, Any]:
    """
    Загрузить конфигурацию из YAML файла.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Dict с конфигурацией
        
    Raises:
        FileNotFoundError: Если файл конфигурации не найден
        yaml.YAMLError: Если файл содержит невалидный YAML
    """
    global _config
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Конфигурационный файл {config_path} не найден")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
    
    return _config


def get_config() -> Dict[str, Any]:
    """
    Получить загруженную конфигурацию.
    
    Returns:
        Dict с конфигурацией
        
    Raises:
        RuntimeError: Если конфигурация не загружена
    """
    if _config is None:
        raise RuntimeError("Конфигурация не загружена. Вызовите load_config() сначала.")
    
    return _config

