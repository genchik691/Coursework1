"""Настройка логирования для приложения."""

import logging
from pathlib import Path


def setup_logger(name: str, log_file: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Настраивает логер для указанного модуля.

    Args:
        name: Имя логера (обычно __name__)
        log_file: Имя файла для записи логов
        level: Уровень логирования

    Returns:
        Настроенный логер
    """
    # Создаем директорию logs, если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Полный путь к файлу лога
    log_path = log_dir / log_file

    # Создаем логер
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Очищаем существующие handlers, если есть
    if logger.hasHandlers():
        logger.handlers.clear()

    # Создаем file handler
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Устанавливаем форматтер для handler
    file_handler.setFormatter(formatter)

    # Добавляем handler к логеру
    logger.addHandler(file_handler)

    return logger
