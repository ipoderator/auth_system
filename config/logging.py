"""
Настройка логирования с использованием loguru.
"""
import sys
import inspect
from pathlib import Path
from datetime import datetime
from loguru import logger
import pytz

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Директория для логов
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Удаляем стандартный обработчик loguru
logger.remove()

# Фильтр для добавления московского времени в каждую запись
def add_moscow_time(record):
    """Добавляет отформатированное московское время в record."""
    # Получаем текущее время записи
    dt = datetime.fromtimestamp(record["time"].timestamp(), tz=pytz.UTC)
    moscow_dt = dt.astimezone(MOSCOW_TZ)
    
    # Добавляем отформатированное московское время для вывода в лог
    record["extra"]["time_formatted"] = moscow_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Модифицируем record["time"] для использования московского времени в имени файла
    # Создаем новый datetime объект без timezone для совместимости с loguru
    moscow_dt_naive = moscow_dt.replace(tzinfo=None)
    # Обновляем время в record для использования в паттерне имени файла
    record["time"] = moscow_dt_naive
    
    return True  # Фильтр должен возвращать True для пропуска записи

# Настройка формата логов
LOG_FORMAT = (
    "<green>{extra[time_formatted]}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Формат для файлов (без цветов)
LOG_FILE_FORMAT = (
    "{extra[time_formatted]} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

# Настройка обработчиков
# 1. Консольный вывод (только для DEBUG и выше)
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level="DEBUG",
    colorize=True,
    backtrace=True,
    diagnose=True,
    filter=add_moscow_time,
)

# 2. Общий лог файл (все уровни)
# Используем стандартный путь с паттерном времени
# Фильтр будет добавлять московское время в формат
logger.add(
    str(LOGS_DIR / "app_{time:YYYY-MM-DD}.log"),
    format=LOG_FILE_FORMAT,
    level="DEBUG",
    rotation="00:00",  # Ротация в полночь
    retention="30 days",  # Хранить логи 30 дней
    compression="zip",  # Сжимать старые логи
    backtrace=True,
    diagnose=True,
    encoding="utf-8",
    filter=add_moscow_time,
)

# 3. Отдельный файл для ошибок
logger.add(
    str(LOGS_DIR / "errors_{time:YYYY-MM-DD}.log"),
    format=LOG_FILE_FORMAT,
    level="ERROR",
    rotation="00:00",
    retention="90 days",  # Ошибки храним дольше
    compression="zip",
    backtrace=True,
    diagnose=True,
    encoding="utf-8",
    filter=add_moscow_time,
)

# Настройка для интеграции со стандартным logging Django
# Перехватываем сообщения из стандартного logging
import logging


class InterceptHandler(logging.Handler):
    """
    Перехватывает сообщения из стандартного logging и перенаправляет их в loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Получаем соответствующий уровень loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Находим вызывающий фрейм
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """
    Настраивает логирование для Django приложения.
    """
    # Отключаем стандартные логи Django
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Отключаем логирование от некоторых библиотек (опционально)
    logger.disable("urllib3")
    logger.disable("requests.packages.urllib3")

    # Включаем логирование для нашего приложения
    logger.enable("apps")
    logger.enable("config")

    return logger

