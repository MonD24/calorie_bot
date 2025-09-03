# -*- coding: utf-8 -*-
"""
Конфигурационный файл для калорийного бота
"""
import os
from pathlib import Path

# Загружаем переменные окружения из .env файла (если есть)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv не установлен, используем только системные переменные окружения
    pass

# API ключи (приоритет: переменные окружения -> значения по умолчанию)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')

# ВАЖНО: Для продакшена установите токены через переменные окружения или .env файл!
# Никогда не делитесь этими токенами и не коммитьте их в git!
# 
# Получить токены:
# - Telegram Bot Token: https://t.me/BotFather
# - OpenAI API Key: https://platform.openai.com/api-keys

# Папка для данных
DATA_DIR = os.getenv('DATA_DIR', 'bot_data')

# Уровень логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Файл логов
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# Расписание заданий (UTC время)
SCHEDULE = {
    'morning_weight': {'hour': 3, 'minute': 0},  # 6:00 МСК
    'evening_summary': {'hour': 18, 'minute': 0},  # 21:00 МСК
}

# Лимиты валидации
VALIDATION_LIMITS = {
    'weight': {'min': 30, 'max': 300},
    'height': {'min': 100, 'max': 250},
    'age': {'min': 10, 'max': 120},
    'calories': {'min': 10, 'max': 5000},
}

# Коэффициенты для расчета калорий
ACTIVITY_MULTIPLIER = 1.375  # Умеренная активность
GOAL_MULTIPLIERS = {
    'deficit': 0.8,   # -20% для похудения
    'maintain': 1.0,  # Поддержание веса
    'surplus': 1.1,   # +10% для набора массы
}
