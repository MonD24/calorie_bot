#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл калорийного бота - calorie_bot_modular.py
"""
import logging
import os
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TELEGRAM_BOT_TOKEN
from handlers.commands import (
    start_command, help_command, goal_command, 
    weight_command, burn_command, left_command,
    clear_today_command, reset_command, limit_command
)
from handlers.text_handler import handle_text_message
from handlers.photo_handler import handle_photo_message
from handlers.callback_handler import handle_callback_query

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("goal", goal_command))
        application.add_handler(CommandHandler("weight", weight_command))
        application.add_handler(CommandHandler("burn", burn_command))
        application.add_handler(CommandHandler("left", left_command))
        application.add_handler(CommandHandler("clear", clear_today_command))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(CommandHandler("limit", limit_command))
        
        # Добавляем обработчики сообщений
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        # Добавляем обработчик callback запросов
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        logger.info("🚀 Бот запущен!")
        print("🚀 Калорийный бот запущен и готов к работе!")
        print("📱 Для остановки нажмите Ctrl+C")
        
        # Запускаем бота
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)
