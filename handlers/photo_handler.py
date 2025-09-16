# -*- coding: utf-8 -*-
"""
Обработчик фото еды
"""
import base64
import os
import datetime
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Блокируем старые методы OpenAI
import openai_safe

from utils.user_data import (
    get_user_profile, get_user_diary, save_user_diary,
    get_user_food_log, save_user_food_log, get_user_burned
)
from utils.photo_processor import analyze_food_photo
from utils.calorie_calculator import get_calories_left_message


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото еды"""
    user_id = str(update.effective_user.id)
    today = datetime.date.today().isoformat()

    try:
        # Получаем файл фото
        file = await update.message.photo[-1].get_file()
        file_name = f'temp_{user_id}.jpg'

        # Загружаем файл
        await file.download_to_drive(file_name)

        # Конвертируем в base64
        with open(file_name, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Удаляем временный файл
        os.remove(file_name)

        # Отправляем сообщение о начале анализа
        analyzing_msg = await update.message.reply_text('🔍 Анализирую фото...')

        # Анализируем фото через GPT
        result = await analyze_food_photo(img_b64)

        if 'error' in result:
            await analyzing_msg.edit_text(
                f'❌ {result["error"]}\n\nОпишите блюдо текстом для расчета калорий.'
            )
            return

        if 'question' in result:
            # GPT задал уточняющий вопрос
            await analyzing_msg.edit_text(result['question'])
            context.user_data['pending_photo_base64'] = img_b64
            context.user_data['waiting_for_photo_clarification'] = True
            return

        if result.get('success'):
            # Успешно проанализировали
            description = result['description']
            kcal = result['calories']
            protein = result.get('protein')
            fat = result.get('fat')
            carbs = result.get('carbs')

            # Предлагаем подтвердить или уточнить
            keyboard = [
                [InlineKeyboardButton('✅ Подтвердить', callback_data='confirm_photo')],
                [InlineKeyboardButton('✏️ Уточнить', callback_data='edit_photo')]
            ]

            # Формируем текст с полными БЖУ
            nutrition_parts = [f'🔥 **Калории:** {kcal} ккал']
            if protein is not None:
                nutrition_parts.append(f'🥩 **Белок:** {protein:.1f} г')
            if fat is not None:
                nutrition_parts.append(f'🧈 **Жиры:** {fat:.1f} г')
            if carbs is not None:
                nutrition_parts.append(f'🍞 **Углеводы:** {carbs:.1f} г')

            nutrition_text = '\n'.join(nutrition_parts)

            await analyzing_msg.edit_text(
                f'📸 **Распознано:**\n{description}\n\n{nutrition_text}\n\nВерно?',
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

            # Сохраняем данные для подтверждения
            dish_data = {
                'description': description,
                'kcal': kcal,
                'protein': protein,
                'fat': fat,
                'carbs': carbs
            }

            context.user_data['pending_photo_dish'] = dish_data
            context.user_data['pending_photo_base64'] = img_b64

        else:
            await analyzing_msg.edit_text(
                '❌ Не удалось проанализировать фото.\n\nОпишите блюдо текстом для расчета калорий.'
            )

    except Exception as e:
        logging.error(f"Error processing photo: {e}")
        await update.message.reply_text(
            f'❌ Ошибка при обработке фото:\n'
            f'`{str(e)}`\n\n'
            f'Тип ошибки: {type(e).__name__}\n'
            f'Опишите блюдо текстом для расчета калорий или обратитесь к разработчику.'
        )


async def handle_photo_confirmation(update, context, user_id, confirm: bool):
    """Обработка подтверждения или уточнения фото"""
    today = datetime.date.today().isoformat()

    if confirm:
        # Подтверждение распознанного блюда
        dish_data = context.user_data.get('pending_photo_dish', {})
        description = dish_data.get('description', 'Блюдо с фото')
        kcal = dish_data.get('kcal', 0)
        protein = dish_data.get('protein')
        fat = dish_data.get('fat')
        carbs = dish_data.get('carbs')

        if kcal:
            # Сохраняем данные
            diary = get_user_diary(user_id)
            food_log = get_user_food_log(user_id)
            profile = get_user_profile(user_id)

            diary[today] = diary.get(today, 0) + kcal
            save_user_diary(user_id, diary)

            if today not in food_log:
                food_log[today] = []
            # Добавляем запись с полными БЖУ
            log_entry = [description, kcal, protein, fat, carbs]
            food_log[today].append(log_entry)
            save_user_food_log(user_id, food_log)

            # Рассчитываем остаток
            burned = get_user_burned(user_id)
            left_message = get_calories_left_message(profile, diary, burned, today)

            # Формируем сообщение с полными БЖУ
            nutrition_parts = [f'{kcal} ккал']
            if protein:
                nutrition_parts.append(f'{protein:.1f}г белка')
            if fat:
                nutrition_parts.append(f'{fat:.1f}г жиров')
            if carbs:
                nutrition_parts.append(f'{carbs:.1f}г углеводов')

            nutrition_text = ', '.join(nutrition_parts)
            response_text = f'✅ Добавлено: {description}, {nutrition_text}. {left_message}'

            keyboard = [[InlineKeyboardButton('Сколько осталось калорий?', callback_data='check_left')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            response_text = '❌ Ошибка при сохранении данных'
            reply_markup = None

        # Очищаем временные данные
        context.user_data.pop('pending_photo_dish', None)
        context.user_data.pop('pending_photo_base64', None)

        return response_text, reply_markup

    else:
        # Запрос уточнения
        context.user_data['waiting_for_photo_clarification'] = True
        return 'Опишите что на фото (текстом):', None


async def handle_photo_clarification(update, context, user_id, clarification_text):
    """Обработка уточнения по фото"""
    # Здесь можно добавить логику повторного анализа с учетом уточнения
    # Пока что просто используем текстовое описание
    from .text_handler import handle_food_input

    today = datetime.date.today().isoformat()
    diary = get_user_diary(user_id)
    food_log = get_user_food_log(user_id)
    profile = get_user_profile(user_id)

    await handle_food_input(update, context, clarification_text, user_id, today, diary, food_log, profile)

    # Сбрасываем флаги
    context.user_data['waiting_for_photo_clarification'] = False
    context.user_data.pop('pending_photo_base64', None)

# Алиас для совместимости
handle_photo = handle_photo_message
