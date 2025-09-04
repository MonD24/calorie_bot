# -*- coding: utf-8 -*-
"""
Обработчики команд бота
"""
import datetime
import logging
import traceback
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.user_data import (
    get_user_profile, save_user_profile, get_user_diary, save_user_diary, 
    get_user_burned, get_user_food_log, save_user_food_log, save_user_burned
)
from utils.calorie_calculator import calculate_bmr_tdee, get_calories_left_message
from config import VALIDATION_LIMITS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - регистрация или приветствие"""
    user_id = str(update.effective_user.id)
    profile = get_user_profile(user_id)

    # Проверяем, есть ли уже профиль пользователя
    if not profile or ('target_calories' not in profile and 'norm' not in profile):
        # Если профиля нет, начинаем регистрацию
        profile = {}
        save_user_profile(user_id, profile)
        await update.message.reply_text('Привет! Введи свой вес (кг):')
        context.user_data['step'] = 'weight'
    else:
        # Если профиль уже есть, показываем информацию
        await show_user_status(update, user_id)
        context.user_data['step'] = 'food'


async def show_user_status(update: Update, user_id: str):
    """Показывает статус пользователя"""
    profile = get_user_profile(user_id)
    diary = get_user_diary(user_id)
    burned = get_user_burned(user_id)
    today = datetime.date.today().isoformat()
    
    # Инициализируем дневник на сегодня, если записи ещё нет
    if today not in diary:
        diary[today] = 0
        from ..utils.user_data import save_user_diary
        save_user_diary(user_id, diary)
    
    eaten_today = diary.get(today, 0)
    burned_today = burned.get(today, 0)
    
    # Получаем параметры для отображения
    target_calories = profile.get('target_calories')
    bmr = profile.get('bmr', 0)
    tdee = profile.get('tdee', 0)
    goal = profile.get('goal', 'deficit')
    
    goal_names = {
        'deficit': '🔥 Похудение',
        'maintain': '⚖️ Поддержание веса',
        'surplus': '💪 Набор массы'
    }
    goal_name = goal_names.get(goal, 'Не указана')
    
    # Получаем сообщение об остатке калорий
    left_message = get_calories_left_message(profile, diary, burned, today)

    if target_calories:
        # Новая система с автоматическим расчётом
        net_calories = eaten_today - burned_today
        
        status_msg = f"""🔥 С возвращением!

📊 Ваши параметры:
📈 Основной обмен (BMR): {bmr} ккал
🔥 Суточный расход (TDEE): {tdee} ккал
🎯 Цель: {goal_name}
🍽️ Целевая норма: {target_calories} ккал

📝 Сегодня:
🍽️ Съедено: {eaten_today} ккал
🏃 Потрачено: {burned_today} ккал
⚖️ Чистые калории: {net_calories} ккал
✨ {left_message}"""
    else:
        # Старая система (для совместимости)
        norm = profile.get('norm', 0)
        target_limit = profile.get('target_limit')
        
        if target_limit:
            net_calories = eaten_today - burned_today
            deficit = norm - target_limit

            status_msg = f"""🔥 С возвращением!

📊 Ваши параметры (старая система):
📈 Основной обмен: {norm} ккал
🎯 Целевой лимит: {target_limit} ккал
🔥 Дефицит: {deficit} ккал

📝 Сегодня:
🍽️ Съедено: {eaten_today} ккал
🏃 Потрачено: {burned_today} ккал
⚖️ Чистые калории: {net_calories} ккал
✨ {left_message}"""
        else:
            status_msg = f"""🔥 С возвращением!

📈 Ваша норма: {norm} ккал
📝 Съедено сегодня: {eaten_today} ккал
🏃 Потрачено: {burned_today} ккал
✨ {left_message}

💡 Используйте /goal для выбора цели и автоматического расчёта калорий"""

    status_msg += "\n\nОтправляйте фото еды или пишите текстом что едите!"

    await update.message.reply_text(
        status_msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Сколько осталось калорий?', callback_data='check_left')]
        ])
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка"""
    help_text = """🤖 *Калорийный бот - справка*

📋 *Основные команды:*
/start - Начать работу или показать статус
/help - Эта справка
/goal - Установить цель (похудение/поддержание/набор массы)
/weight - Записать текущий вес
/burn - Записать потраченные калории
/left - Узнать остаток калорий на день
/food - Показать дневник еды за день
/clear\_today - Очистить записи за сегодня
/reset - Сбросить профиль (начать заново)
/limit - Установить лимит калорий (старая система)

🍽️ *Как добавлять еду:*
• Отправьте фото блюда для автоматического анализа
• Напишите текстом что едите, например: "творог с арбузом"
• Бот автоматически рассчитает калории

🎯 *Система целей:*
🔥 Похудение - дефицит 20% от нормы
⚖️ Поддержание веса - норма калорий  
💪 Набор массы - профицит 10% от нормы

⏰ *Автоматические функции:*
• Утреннее напоминание о весе (6:00 МСК)
• Вечерний итог дня (21:00 МСК)
• Умные подсказки и валидация данных

💡 *Совет:* Для быстрого доступа к командам начните вводить "/" в поле сообщения"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /goal - установка цели"""
    keyboard = [
        [InlineKeyboardButton('🔥 Похудение (дефицит 20%)', callback_data='goal_deficit')],
        [InlineKeyboardButton('⚖️ Поддержание веса', callback_data='goal_maintain')],
        [InlineKeyboardButton('💪 Набор массы (профицит 10%)', callback_data='goal_surplus')]
    ]
    
    await update.message.reply_text(
        '🎯 Выберите вашу цель:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def weight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /weight - запись веса"""
    await update.message.reply_text('Введите ваш текущий вес (кг):')
    context.user_data['step'] = 'daily_weight'


async def burn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /burn - запись потраченных калорий"""
    await update.message.reply_text('Сколько калорий потратили сегодня?')
    context.user_data['step'] = 'burn_calories'


async def left_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /left - остаток калорий"""
    user_id = str(update.effective_user.id)
    profile = get_user_profile(user_id)
    diary = get_user_diary(user_id)
    burned = get_user_burned(user_id)
    today = datetime.date.today().isoformat()
    
    left_message = get_calories_left_message(profile, diary, burned, today)
    await update.message.reply_text(left_message)


async def clear_today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear_today - очистка записей за день"""
    user_id = str(update.effective_user.id)
    today = datetime.date.today().isoformat()
    
    # Очищаем данные за сегодня
    diary = get_user_diary(user_id)
    food_log = get_user_food_log(user_id)
    burned = get_user_burned(user_id)
    
    diary[today] = 0
    food_log[today] = []
    burned[today] = 0
    
    save_user_diary(user_id, diary)
    save_user_food_log(user_id, food_log)
    save_user_burned(user_id, burned)
    
    await update.message.reply_text('✅ Записи за сегодня очищены!')


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reset - сброс профиля"""
    keyboard = [
        [InlineKeyboardButton('✅ Да, сбросить', callback_data='confirm_reset')],
        [InlineKeyboardButton('❌ Отмена', callback_data='cancel_reset')]
    ]
    
    await update.message.reply_text(
        '⚠️ Вы уверены что хотите сбросить все данные профиля?\n'
        'Это действие нельзя отменить!',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /limit - установка лимита калорий (устаревшая)"""
    await update.message.reply_text(
        '⚠️ Команда /limit устарела!\n\n'
        'Используйте /goal для автоматического расчета калорий на основе ваших параметров и цели.'
    )


async def food_log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /food - показать дневной журнал еды"""
    user_id = str(update.effective_user.id)
    today = datetime.date.today().isoformat()
    
    # DEBUG: Добавляем детальное логирование
    logging.info(f"🔍 DEBUG food_log_command: Пользователь {user_id}, дата {today}")
    
    try:
        food_log = get_user_food_log(user_id)
        logging.info(f"🔍 DEBUG food_log_command: Полный food_log = {food_log}")
        logging.info(f"🔍 DEBUG food_log_command: Тип food_log = {type(food_log)}")
        logging.info(f"🔍 DEBUG food_log_command: Ключи в food_log = {list(food_log.keys())}")
        
        today_foods = food_log.get(today, [])
        logging.info(f"🔍 DEBUG food_log_command: Еда за {today} = {today_foods}")
        logging.info(f"🔍 DEBUG food_log_command: Количество записей = {len(today_foods)}")
        
        if not today_foods:
            logging.info("🔍 DEBUG food_log_command: Нет записей, отправляем сообщение")
            await update.message.reply_text('📝 Сегодня пока ничего не записано.')
            logging.info("🔍 DEBUG food_log_command: Сообщение о пустом дневнике отправлено")
            return
        
        # Создаем детальный обзор
        message_lines = ['📋 **Дневник еды:**\n']
        total_calories = 0
        total_protein = 0
        
        for i, food_entry in enumerate(today_foods, 1):
            logging.info(f"🔍 DEBUG food_log_command: Обрабатываем запись {i}: {food_entry}")
            
            if len(food_entry) >= 3:  # Новый формат с белком
                name, calories, protein = food_entry[0], food_entry[1], food_entry[2]
                protein_text = f', {protein}г белка' if protein else ''
                logging.info(f"🔍 DEBUG food_log_command: Новый формат - {name}, {calories}ккал, {protein}г белка")
            elif len(food_entry) >= 2:  # Старый формат без белка
                name, calories = food_entry[0], food_entry[1]
                protein = 0
                protein_text = ''
                logging.info(f"🔍 DEBUG food_log_command: Старый формат - {name}, {calories}ккал")
            else:
                logging.warning(f"🔍 DEBUG food_log_command: Неправильный формат записи: {food_entry}")
                continue
            
            total_calories += calories
            if protein:
                total_protein += protein
            
            message_lines.append(f'{i}. {name}: {calories} ккал{protein_text}')
        
        # Добавляем итоги
        message_lines.append(f'\n**Итого за день:**')
        message_lines.append(f'🔥 Калории: {total_calories} ккал')
        if total_protein > 0:
            message_lines.append(f'💪 Белок: {total_protein}г')
        
        message_text = '\n'.join(message_lines)
        logging.info(f"🔍 DEBUG food_log_command: Готовое сообщение длиной {len(message_text)} символов")
        logging.info(f"🔍 DEBUG food_log_command: Отправляем: {message_text}")
        
        await update.message.reply_text(message_text, parse_mode='Markdown')
        logging.info("🔍 DEBUG food_log_command: Сообщение отправлено УСПЕШНО!")
        
    except Exception as e:
        logging.error(f"🔍 DEBUG food_log_command: ОШИБКА - {e}")
        logging.error(f"🔍 DEBUG food_log_command: Traceback - {traceback.format_exc()}")
        await update.message.reply_text(f'❌ Ошибка при получении дневника: {str(e)}')


async def evening_summary_function(context, user_id):
    """Функция для автоматического вечернего обзора"""
    today = datetime.date.today().isoformat()
    
    food_log = get_user_food_log(user_id)
    today_foods = food_log.get(today, [])
    
    if not today_foods:
        message = '🌙 **Вечерний обзор**\n\n📝 Сегодня ничего не записано в дневник.'
    else:
        # Создаем обзор
        message_lines = ['🌙 **Вечерний обзор дня**\n']
        total_calories = 0
        total_protein = 0
        
        for food_entry in today_foods:
            if len(food_entry) >= 3:  # Новый формат с белком
                name, calories, protein = food_entry[0], food_entry[1], food_entry[2]
            elif len(food_entry) >= 2:  # Старый формат без белка
                name, calories = food_entry[0], food_entry[1]
                protein = 0
            else:
                continue
                
            total_calories += calories
            if protein:
                total_protein += protein
        
        message_lines.append(f'🔥 Всего калорий: {total_calories} ккал')
        if total_protein > 0:
            message_lines.append(f'💪 Всего белка: {total_protein}г')
        
        message_lines.append(f'\n📝 Записей в дневнике: {len(today_foods)}')
        
        # Добавляем остаток калорий
        profile = get_user_profile(user_id)
        diary = get_user_diary(user_id)
        burned = get_user_burned(user_id)
        left_message = get_calories_left_message(profile, diary, burned, today)
        message_lines.append(f'\n{left_message}')
        
        message = '\n'.join(message_lines)
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Failed to send evening summary to {user_id}: {e}")


async def morning_weight_function(context, user_id):
    """Функция для автоматического утреннего запроса веса"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text='🌅 **Доброе утро!**\n\n⚖️ Введите ваш текущий вес (кг):',
            parse_mode='Markdown'
        )
        # Устанавливаем ожидание ввода веса
        context.user_data['step'] = 'daily_weight'
    except Exception as e:
        logging.error(f"Failed to send morning weight request to {user_id}: {e}")
