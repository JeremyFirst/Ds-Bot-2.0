"""
Утилиты для работы с временными зонами.
В БД всегда хранится UTC, конвертация в UTC+3 только для UI.
"""

from datetime import datetime, timezone, timedelta


UTC3 = timezone(timedelta(hours=3))


def utc_to_utc3(utc_dt: datetime) -> datetime:
    """
    Конвертировать UTC время в UTC+3.
    
    Args:
        utc_dt: datetime в UTC (без timezone или с UTC timezone)
        
    Returns:
        datetime в UTC+3
    """
    if utc_dt.tzinfo is None:
        # Если timezone не указан, считаем что это UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    return utc_dt.astimezone(UTC3)


def format_datetime_utc3(utc_dt: datetime, format_str: str = "%d.%m.%Y %H:%M:%S") -> str:
    """
    Форматировать UTC datetime в строку UTC+3.
    
    Args:
        utc_dt: datetime в UTC
        format_str: Формат строки (по умолчанию "%d.%m.%Y %H:%M:%S")
        
    Returns:
        Отформатированная строка в UTC+3
    """
    utc3_dt = utc_to_utc3(utc_dt)
    return utc3_dt.strftime(format_str)

