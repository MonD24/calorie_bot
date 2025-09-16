#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл калорийного бота - calorie_bot_modular.py
"""
import logging
import os
import sys
import datetime
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import JobQueue

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Блокируем старые методы OpenAI
import openai_safe

from config import TELEGRAM_BOT_TOKEN, SCHEDULE
from handlers.commands import (
    start_command, help_command, goal_command, 
    weight_command, burn_command, left_command,
    clear_today_command, reset_command, limit_command, food_log_command,
    macros_command, evening_summary_function, morning_weight_function
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


async def send_morning_weight_message(context):
    """Отправка утреннего сообщения о весе всем пользователям"""
    from utils.user_data import get_all_users
    
    try:
        user_ids = get_all_users()
        for user_id in user_ids:
            try:
                await morning_weight_function(context, user_id)
            except Exception as e:
                logger.error(f"Failed to send morning message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in send_morning_weight_message: {e}")


async def send_evening_summary_message(context):
    """Отправка вечернего обзора всем пользователям"""
    from utils.user_data import get_all_users
    
    try:
        user_ids = get_all_users()
        for user_id in user_ids:
            try:
                await evening_summary_function(context, user_id)
            except Exception as e:
                logger.error(f"Failed to send evening summary to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in send_evening_summary_message: {e}")


def setup_scheduled_jobs(application):
    """Настройка автоматических заданий"""
    job_queue = application.job_queue
    
    # Утреннее напоминание о весе
    morning_time = datetime.time(
        hour=SCHEDULE['morning_weight']['hour'],
        minute=SCHEDULE['morning_weight']['minute']
    )
    job_queue.run_daily(
        send_morning_weight_message,
        time=morning_time,
        name='morning_weight'
    )
    
    # Вечерний обзор дня
    evening_time = datetime.time(
        hour=SCHEDULE['evening_summary']['hour'],
        minute=SCHEDULE['evening_summary']['minute']
    )
    job_queue.run_daily(
        send_evening_summary_message,
        time=evening_time,
        name='evening_summary'
    )
    
    logger.info(f"📅 Scheduled jobs set up: morning {morning_time}, evening {evening_time}")


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
        application.add_handler(CommandHandler("food", food_log_command))
        application.add_handler(CommandHandler("macros", macros_command))
        
        # Добавляем обработчики сообщений
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        # Добавляем обработчик callback запросов
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Настраиваем автоматические задания
        setup_scheduled_jobs(application)
        
        logger.info("🚀 Бот запущен!")
        print("🚀 Калорийный бот запущен и готов к работе!")
        print("📱 Для остановки нажмите Ctrl+C")
        print("⏰ Автоматические сообщения настроены:")
        print(f"   🌅 Утренний запрос веса: {SCHEDULE['morning_weight']['hour']:02d}:{SCHEDULE['morning_weight']['minute']:02d} UTC")
        print(f"   🌙 Вечерний обзор дня: {SCHEDULE['evening_summary']['hour']:02d}:{SCHEDULE['evening_summary']['minute']:02d} UTC")
        
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
