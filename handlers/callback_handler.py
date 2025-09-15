# -*- coding: utf-8 -*-
"""
Обработчик callback кнопок
"""
import datetime
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.user_data import (
    get_user_profile, save_user_profile, get_user_diary, 
    save_user_diary, get_user_weights, save_user_weights,
    get_user_food_log, save_user_food_log, get_user_burned,
    save_user_burned, load_user_data, save_user_data
)
from utils.calorie_calculator import calculate_bmr_tdee, get_calories_left_message


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    user_id = str(update.effective_user.id)
    query = update.callback_query
    today = datetime.date.today().isoformat()

    # Безопасно отвечаем на callback query
    try:
        await query.answer()
    except Exception as e:
        logging.warning(f"Callback query answer failed: {e}")

    if query.data == 'check_left':
        await handle_check_left(query, user_id, today)
    
    elif query.data.startswith('goal_'):
        await handle_goal_selection(query, context, user_id, query.data)
    
    elif query.data.startswith('save_weight_'):
        await handle_save_weight(query, context, user_id, query.data, today)
    
    elif query.data.startswith('save_calories_'):
        await handle_save_calories(query, context, user_id, query.data, today)
    
    elif query.data.startswith('use_yesterday_weight_'):
        await handle_use_yesterday_weight(query, context, user_id, query.data, today)
    
    elif query.data == 'confirm_reset':
        await handle_confirm_reset(query, context, user_id)
    
    elif query.data == 'cancel_reset':
        await handle_cancel_reset(query)
    
    elif query.data == 'cancel_input':
        await handle_cancel_input(query, context)
    
    elif query.data == 'confirm_photo':
        await handle_confirm_photo(query, context, user_id)
    
    elif query.data == 'edit_photo':
        await handle_edit_photo(query, context, user_id)


async def handle_check_left(query, user_id, today):
    """Показать остаток калорий"""
    profile = get_user_profile(user_id)
    diary = get_user_diary(user_id)
    burned = get_user_burned(user_id)
    
    left_message = get_calories_left_message(profile, diary, burned, today)
    
    try:
        await query.edit_message_text(left_message)
    except Exception as e:
        logging.warning(f"Message edit failed: {e}")
        await query.message.reply_text(left_message)


async def handle_goal_selection(query, context, user_id, goal_data):
    """Обработка выбора цели"""
    goal = goal_data.replace('goal_', '')
    profile = get_user_profile(user_id)
    
    # Проверяем, есть ли все необходимые данные для расчета
    required_fields = ['weight', 'height', 'age', 'sex']
    if not all(field in profile for field in required_fields):
        await query.edit_message_text(
            '❌ Для автоматического расчета калорий нужно заполнить профиль.\n'
            'Используйте /start для регистрации.'
        )
        return
    
    # Рассчитываем калории
    calc_result = calculate_bmr_tdee(
        weight=profile['weight'],
        height=profile['height'],
        age=profile['age'],
        sex=profile['sex'],
        goal=goal
    )
    
    # Обновляем профиль
    profile.update(calc_result)
    profile['target_calories'] = calc_result['target']
    # Сбрасываем флаг пользовательского лимита, так как теперь используется автоматический расчет
    profile['custom_limit'] = False
    # Удаляем registration_step, так как регистрация завершена
    if 'registration_step' in profile:
        del profile['registration_step']
    save_user_profile(user_id, profile)
    
    goal_names = {
        'deficit': '🔥 Похудение (дефицит 20%)',
        'maintain': '⚖️ Поддержание веса',
        'surplus': '💪 Набор массы (профицит 10%)'
    }
    goal_name = goal_names.get(goal, 'Неизвестная цель')
    
    success_msg = f"""✅ Цель установлена: {goal_name}

📊 Ваши новые параметры:
📈 Основной обмен (BMR): {calc_result['bmr']} ккал
🔥 Суточный расход (TDEE): {calc_result['tdee']} ккал
🎯 Целевая норма: {calc_result['target']} ккал

Теперь бот будет автоматически отслеживать ваш прогресс!"""
    
    try:
        await query.edit_message_text(success_msg)
    except Exception as e:
        await query.message.reply_text(success_msg)
    
    # Сбрасываем step
    context.user_data['step'] = 'food'


async def handle_save_weight(query, context, user_id, weight_data, today):
    """Сохранение веса из двусмысленного ввода"""
    weight = float(weight_data.replace('save_weight_', ''))
    weights = get_user_weights(user_id)
    weights[today] = weight
    save_user_weights(user_id, weights)
    
    try:
        await query.edit_message_text(f'✅ Вес {weight} кг записан!')
    except Exception as e:
        await query.message.reply_text(f'✅ Вес {weight} кг записан!')
    
    context.user_data.pop('pending_number', None)


async def handle_save_calories(query, context, user_id, calories_data, today):
    """Сохранение калорий из двусмысленного ввода"""
    calories = int(float(calories_data.replace('save_calories_', '')))
    
    # Сохраняем как съеденные калории
    diary = get_user_diary(user_id)
    food_log = get_user_food_log(user_id)
    profile = get_user_profile(user_id)
    
    diary[today] = diary.get(today, 0) + calories
    save_user_diary(user_id, diary)
    
    if today not in food_log:
        food_log[today] = []
    food_log[today].append([f'Еда ({calories} ккал)', calories])
    save_user_food_log(user_id, food_log)
    
    # Рассчитываем остаток
    burned = get_user_burned(user_id)
    left_message = get_calories_left_message(profile, diary, burned, today)
    
    try:
        await query.edit_message_text(f'✅ Добавлено {calories} ккал. {left_message}')
    except Exception as e:
        await query.message.reply_text(f'✅ Добавлено {calories} ккал. {left_message}')
    
    context.user_data.pop('pending_number', None)


async def handle_use_yesterday_weight(query, context, user_id, weight_data, today):
    """Использование вчерашнего веса"""
    weight = float(weight_data.replace('use_yesterday_weight_', ''))
    weights = get_user_weights(user_id)
    weights[today] = weight
    save_user_weights(user_id, weights)
    
    try:
        await query.edit_message_text(f'✅ Вес {weight} кг записан (как вчера)!')
    except Exception as e:
        await query.message.reply_text(f'✅ Вес {weight} кг записан (как вчера)!')
    
    context.user_data['step'] = None


async def handle_confirm_reset(query, context, user_id):
    """Подтверждение сброса профиля"""
    # Удаляем все данные пользователя
    empty_data = {
        'profile': {},
        'diary': {},
        'weights': {},
        'food_log': {},
        'burned': {}
    }
    save_user_data(user_id, empty_data)
    
    try:
        await query.edit_message_text(
            '✅ Профиль сброшен!\n\nИспользуйте /start для новой регистрации.'
        )
    except Exception as e:
        await query.message.reply_text(
            '✅ Профиль сброшен!\n\nИспользуйте /start для новой регистрации.'
        )
    
    # Очищаем состояние
    context.user_data.clear()


async def handle_cancel_reset(query):
    """Отмена сброса профиля"""
    try:
        await query.edit_message_text('❌ Сброс профиля отменен.')
    except Exception as e:
        await query.message.reply_text('❌ Сброс профиля отменен.')


async def handle_cancel_input(query, context):
    """Отмена ввода"""
    try:
        await query.edit_message_text('❌ Ввод отменен.')
    except Exception as e:
        await query.message.reply_text('❌ Ввод отменен.')
    
    context.user_data.pop('pending_number', None)


async def handle_confirm_photo(query, context, user_id):
    """Подтверждение распознанного блюда с фото"""
    from .photo_handler import handle_photo_confirmation
    
    try:
        response_text, reply_markup = await handle_photo_confirmation(
            None, context, user_id, confirm=True
        )
        await query.edit_message_text(response_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error confirming photo: {e}")
        await query.message.reply_text(
            f'❌ Ошибка при подтверждении фото:\n'
            f'`{str(e)}`\n\n'
            f'Тип ошибки: {type(e).__name__}\n'
            f'Попробуйте ещё раз или обратитесь к разработчику.'
        )


async def handle_edit_photo(query, context, user_id):
    """Запрос уточнения для фото"""
    from .photo_handler import handle_photo_confirmation
    
    try:
        response_text, reply_markup = await handle_photo_confirmation(
            None, context, user_id, confirm=False
        )
        await query.edit_message_text(response_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error editing photo: {e}")
        await query.message.reply_text(
            f'❌ Ошибка при редактировании фото:\n'
            f'`{str(e)}`\n\n'
            f'Тип ошибки: {type(e).__name__}\n'
            f'Попробуйте ещё раз или обратитесь к разработчику.'
        )

# Алиас для совместимости
handle_callback = handle_callback_query
