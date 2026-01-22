# -*- coding: utf-8 -*-
"""
Обработчик текстовых сообщений
"""
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
    get_user_profile, save_user_profile, get_user_diary,
    save_user_diary, get_user_weights, save_user_weights,
    get_user_food_log, save_user_food_log, get_user_burned, save_user_burned,
    add_saved_meal
)
from utils.calorie_calculator import (
    create_calorie_prompt, ask_gpt, extract_nutrition_smart,
    validate_calorie_result, get_calories_left_message,
    calculate_bmr_tdee
)
from utils.error_handler import format_error_message, log_detailed_error
from config import VALIDATION_LIMITS


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = str(update.effective_user.id)
    step = context.user_data.get('step')
    text = update.message.text.strip()
    today = datetime.date.today().isoformat()

    # Получаем данные пользователя
    profile = get_user_profile(user_id)
    diary = get_user_diary(user_id)
    weights = get_user_weights(user_id)
    food_log = get_user_food_log(user_id)

    # Проверяем, есть ли сохраненный шаг регистрации в профиле
    if not step and profile and 'registration_step' in profile:
        step = profile['registration_step']
        context.user_data['step'] = step

    # Инициализируем дневник на сегодня, если записи ещё нет
    if today not in diary:
        diary[today] = 0
        save_user_diary(user_id, diary)

    # === РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ===
    if step == 'weight':
        await handle_weight_input(update, context, text, profile, user_id)
        return
    elif step == 'height':
        await handle_height_input(update, context, text, profile, user_id)
        return
    elif step == 'age':
        await handle_age_input(update, context, text, profile, user_id)
        return
    elif step == 'sex':
        await handle_sex_input(update, context, text, profile, user_id)
        return

    # === ЕЖЕДНЕВНЫЕ ОПЕРАЦИИ ===
    elif step == 'daily_weight':
        await handle_daily_weight(update, context, text, weights, user_id, today)
        return
    elif step == 'burn_calories':
        await handle_burn_calories(update, context, text, user_id, today)
        return
    elif step == 'save_meal_nutrition':
        await handle_save_meal_nutrition(update, context, text, user_id)
        return

    # === ОБРАБОТКА ЕДЫ ===
    elif step == 'food' or step is None:
        await handle_food_input(update, context, text, user_id, today, diary, food_log, profile)
        return

    # === СПЕЦИАЛЬНЫЕ СОСТОЯНИЯ ===
    elif context.user_data.get('waiting_for_clarification'):
        await handle_food_clarification(update, context, text, user_id, today, diary, food_log, profile)
        return

    # Если не попали ни в один case
    await update.message.reply_text(
        'Не понял, что вы хотите сделать. Используйте /help для справки.'
    )


async def handle_weight_input(update, context, text, profile, user_id):
    """Обработка ввода веса при регистрации"""
    try:
        weight = float(text.replace(',', '.'))
        limits = VALIDATION_LIMITS['weight']
        if limits['min'] <= weight <= limits['max']:
            profile['weight'] = weight
            profile['registration_step'] = 'height'
            save_user_profile(user_id, profile)
            await update.message.reply_text('Теперь введи свой рост (см):')
            context.user_data['step'] = 'height'
        else:
            await update.message.reply_text(f'Введите реальный вес от {limits["min"]} до {limits["max"]} кг')
    except ValueError:
        await update.message.reply_text('Введите вес в кг, например: 70')


async def handle_height_input(update, context, text, profile, user_id):
    """Обработка ввода роста при регистрации"""
    try:
        height = float(text.replace(',', '.'))
        limits = VALIDATION_LIMITS['height']
        if limits['min'] <= height <= limits['max']:
            profile['height'] = height
            profile['registration_step'] = 'age'
            save_user_profile(user_id, profile)
            await update.message.reply_text('Теперь введи свой возраст:')
            context.user_data['step'] = 'age'
        else:
            await update.message.reply_text(f'Введите реальный рост от {limits["min"]} до {limits["max"]} см')
    except ValueError:
        await update.message.reply_text('Введите рост в см, например: 175')


async def handle_age_input(update, context, text, profile, user_id):
    """Обработка ввода возраста при регистрации"""
    try:
        age = int(text)
        limits = VALIDATION_LIMITS['age']
        if limits['min'] <= age <= limits['max']:
            profile['age'] = age
            profile['registration_step'] = 'sex'
            save_user_profile(user_id, profile)
            await update.message.reply_text('Укажи пол (муж/жен):')
            context.user_data['step'] = 'sex'
        else:
            await update.message.reply_text(f'Введите реальный возраст от {limits["min"]} до {limits["max"]} лет')
    except ValueError:
        await update.message.reply_text('Введите возраст целым числом, например: 30')


async def handle_sex_input(update, context, text, profile, user_id):
    """Обработка ввода пола при регистрации"""
    sex = text.lower()
    if sex not in ['муж', 'жен']:
        await update.message.reply_text('Введите "муж" или "жен"')
        return

    profile['sex'] = sex
    profile['registration_step'] = 'goal'
    save_user_profile(user_id, profile)

    # Теперь спрашиваем о цели
    keyboard = [
        [InlineKeyboardButton('🔥 Похудение (дефицит 20%)', callback_data='goal_deficit')],
        [InlineKeyboardButton('⚖️ Поддержание веса', callback_data='goal_maintain')],
        [InlineKeyboardButton('💪 Набор массы (профицит 10%)', callback_data='goal_surplus')]
    ]

    await update.message.reply_text(
        '🎯 Выберите вашу цель:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['step'] = 'goal'


async def handle_daily_weight(update, context, text, weights, user_id, today):
    """Обработка ввода ежедневного веса"""
    try:
        weight = float(text.replace(',', '.'))
        limits = VALIDATION_LIMITS['weight']
        if limits['min'] <= weight <= limits['max']:
            weights[today] = weight
            save_user_weights(user_id, weights)
            logging.info(f"User {user_id} recorded weight: {weight} kg on {today}")
            await update.message.reply_text(f'✅ Вес {weight} кг записан!')
            context.user_data['step'] = None
        else:
            await update.message.reply_text(f'Введите реальный вес от {limits["min"]} до {limits["max"]} кг')
    except ValueError:
        await update.message.reply_text('Введите вес в кг, например: 70')


async def handle_burn_calories(update, context, text, user_id, today):
    """Обработка ввода потраченных калорий"""
    try:
        burned_calories = int(text)
        if 0 <= burned_calories <= 5000:  # Разумные пределы
            burned = get_user_burned(user_id)
            burned[today] = burned_calories
            save_user_burned(user_id, burned)
            await update.message.reply_text(f'✅ Записано: потрачено {burned_calories} ккал')
            context.user_data['step'] = None
        else:
            await update.message.reply_text('Введите количество калорий от 0 до 5000')
    except ValueError:
        await update.message.reply_text('Введите количество потраченных калорий числом, например: 300')


async def handle_save_meal_nutrition(update, context, text, user_id):
    """Обработка ввода БЖУ для сохранения нового блюда"""
    meal_name = context.user_data.get('pending_save_meal')
    
    if not meal_name:
        await update.message.reply_text('❌ Ошибка: название блюда не найдено. Используйте /savemeal [название]')
        context.user_data['step'] = None
        return
    
    try:
        # Парсим ввод: может быть "калории" или "калории белки жиры углеводы"
        parts = text.strip().split()
        
        calories = int(parts[0])
        protein = float(parts[1]) if len(parts) > 1 else None
        fat = float(parts[2]) if len(parts) > 2 else None
        carbs = float(parts[3]) if len(parts) > 3 else None
        
        if not (1 <= calories <= 5000):
            await update.message.reply_text('❌ Калорийность должна быть от 1 до 5000 ккал')
            return
        
        # Сохраняем блюдо
        meal_data = {
            'calories': calories,
            'protein': protein,
            'fat': fat,
            'carbs': carbs
        }
        
        add_saved_meal(user_id, meal_name, meal_data)
        
        # Формируем сообщение
        nutrition_parts = [f'{calories} ккал']
        if protein:
            nutrition_parts.append(f'{protein:.1f}г белка')
        if fat:
            nutrition_parts.append(f'{fat:.1f}г жиров')
        if carbs:
            nutrition_parts.append(f'{carbs:.1f}г углеводов')
        
        await update.message.reply_text(
            f'⭐ Блюдо сохранено!\n\n'
            f'📝 *{meal_name}*\n'
            f'🔥 {", ".join(nutrition_parts)}\n\n'
            f'Теперь вы можете быстро добавить его через /meals',
            parse_mode='Markdown'
        )
        
        # Очищаем состояние
        context.user_data['step'] = None
        context.user_data.pop('pending_save_meal', None)
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            '❌ Неверный формат!\n\n'
            'Введите данные в формате:\n'
            '`калории` или `калории белки жиры углеводы`\n\n'
            'Примеры:\n'
            '• `350` - только калории\n'
            '• `350 25 15 20` - калории, белки, жиры, углеводы',
            parse_mode='Markdown'
        )


def parse_manual_calories(text):
    """Парсит текст на предмет явного указания калорий пользователем

    Поддерживаемые форматы:
    - "шоколадка, 205 ккал"
    - "шоколадка 205 ккал"
    - "шоколадка - 205ккал"
    - "шоколадка: 205 калорий"

    Returns:
        tuple: (food_name, calories) или (None, None) если не найдено
    """
    import re

    # Различные паттерны для поиска калорий
    patterns = [
        r'^(.+?)[,\-:\s]+(\d+)\s*(?:ккал|калори[йяе]|калорий|kcal)\s*$',
        r'^(.+?)\s+(\d+)\s*(?:ккал|калори[йяе]|калорий|kcal)\s*$',
    ]

    text_clean = text.strip()

    for pattern in patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            food_name = match.group(1).strip()
            calories = int(match.group(2))

            # Проверяем разумность значения калорий
            if 1 <= calories <= 5000:  # Разумный диапазон для одного приема пищи
                return food_name, calories

    return None, None


async def handle_food_input(update, context, text, user_id, today, diary, food_log, profile):
    """Обработка описания еды"""
    # Проверяем, не ввел ли пользователь просто число (возможный вес или калории)
    if await handle_ambiguous_number(update, context, text):
        return

    # Проверяем, не указал ли пользователь калории в явном виде
    food_name, manual_calories = parse_manual_calories(text)
    if food_name and manual_calories:
        # Пользователь сам указал калории - не обращаемся к GPT
        try:
            # Сохраняем данные напрямую
            diary[today] += manual_calories
            save_user_diary(user_id, diary)

            if today not in food_log:
                food_log[today] = []
            # При ручном вводе БЖУ неизвестны
            food_log[today].append([food_name, manual_calories, None, None, None])
            save_user_food_log(user_id, food_log)

            # Рассчитываем остаток калорий
            burned = get_user_burned(user_id)
            left_message = get_calories_left_message(profile, diary, burned, today)

            await update.message.reply_text(
                f'✅ Записано: {food_name}, {manual_calories} ккал. {left_message}.',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('Сколько осталось калорий?', callback_data='check_left')]
                ])
            )
            return

        except Exception as e:
            log_detailed_error(e, "при сохранении ручного ввода калорий", str(user_id),
                             {"food_name": food_name, "calories": manual_calories})
            error_msg = format_error_message(e, "при сохранении данных",
                                           f'Блюдо: "{food_name}", калории: {manual_calories}')
            await update.message.reply_text(error_msg)
            return

    # Обрабатываем как описание еды через GPT
    try:
        prompt = create_calorie_prompt(text)
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]

        response = await ask_gpt(messages)
        logging.info(f"GPT response for food: {response}")

        # Проверяем, задал ли GPT вопрос
        if "ВОПРОС:" in response:
            question = response.replace("ВОПРОС:", "").strip()
            await update.message.reply_text(question)
            # Сохраняем исходное описание для дальнейшей обработки
            context.user_data['pending_food_description'] = text
            context.user_data['waiting_for_clarification'] = True
            return

        # Извлекаем калории и белок
        nutrition = extract_nutrition_smart(response)
        if not nutrition['calories']:
            await update.message.reply_text('Не удалось распознать калории. Попробуйте описать блюдо подробнее.')
            return

        # Валидируем результат
        kcal = validate_calorie_result(text, nutrition['calories'])
        protein = nutrition.get('protein')
        fat = nutrition.get('fat')
        carbs = nutrition.get('carbs')

        # Сохраняем данные
        diary[today] += kcal
        save_user_diary(user_id, diary)

        if today not in food_log:
            food_log[today] = []
        # Сохраняем в формате: [название, калории, белки, жиры, углеводы]
        food_log[today].append([text, kcal, protein, fat, carbs])
        save_user_food_log(user_id, food_log)

        # Рассчитываем остаток калорий
        burned = get_user_burned(user_id)
        left_message = get_calories_left_message(profile, diary, burned, today)

        # Формируем сообщение с информацией о питании
        nutrition_parts = [f'{kcal} ккал']
        if protein:
            nutrition_parts.append(f'{protein:.1f}г белка')
        if fat:
            nutrition_parts.append(f'{fat:.1f}г жиров')
        if carbs:
            nutrition_parts.append(f'{carbs:.1f}г углеводов')

        nutrition_text = ', '.join(nutrition_parts)

        await update.message.reply_text(
            f'Блюдо: {text}, {nutrition_text}. {left_message}.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Сколько осталось калорий?', callback_data='check_left')]
            ])
        )

    except Exception as e:
        log_detailed_error(e, "при обработке описания еды через GPT", str(user_id),
                         {"user_text": text})
        error_msg = format_error_message(e, "при обработке описания еды", f'Ваш текст: "{text}"')
        await update.message.reply_text(error_msg)


async def handle_ambiguous_number(update, context, text):
    """Обрабатывает ввод числа, которое может быть весом или калориями"""
    try:
        clean_text = text.replace(',', '.').strip()
        if clean_text.replace('.', '').isdigit():
            potential_value = float(clean_text)

            # Если число в пределах возможного веса (30-200 кг)
            if 30 <= potential_value <= 200:
                keyboard = [
                    [InlineKeyboardButton(f'⚖️ Это вес ({potential_value} кг)',
                                          callback_data=f'save_weight_{potential_value}')],
                    [InlineKeyboardButton('🍽️ Это количество калорий',
                                          callback_data=f'save_calories_{potential_value}')],
                    [InlineKeyboardButton('❌ Отмена', callback_data='cancel_input')]
                ]

                await update.message.reply_text(
                    f'Вы ввели число {potential_value}. Что это:\n'
                    f'• Ваш вес в килограммах?\n'
                    f'• Количество калорий?\n'
                    f'Выберите вариант:',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

                context.user_data['pending_number'] = potential_value
                return True

    except ValueError:
        pass

    return False


async def handle_food_clarification(update, context, text, user_id, today, diary, food_log, profile):
    """Обработка уточнений по еде"""
    original_description = context.user_data.get('pending_food_description', '')
    clarification = text

    # Формируем полный запрос с уточнением
    description_prompt = f"""Исходное блюдо: "{original_description}"
Уточнение: "{clarification}"

Создай ПОЛНОЕ описание блюда, сохранив ВСЕ ингредиенты из исходного описания + добавив/заменив согласно уточнению.

Пример:
- Исходное: "творог с чем-то сладким"
- Уточнение: "с арбузом и арахисовой пастой"
- Результат: "творог с арбузом и арахисовой пастой"

Ответь только итоговым описанием:"""

    try:
        # Получаем финальное описание
        description_messages = [{'role': 'user', 'content': [{'type': 'text', 'text': description_prompt}]}]
        final_description = await ask_gpt(description_messages)
        logging.info(f"GPT final description: {final_description}")

        # Рассчитываем калории для финального описания
        prompt = create_calorie_prompt(final_description, is_clarification=True)
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
        response = await ask_gpt(messages)

        nutrition = extract_nutrition_smart(response)
        if not nutrition['calories']:
            await update.message.reply_text('Не удалось распознать калории. Попробуйте ещё раз.')
            return

        kcal = validate_calorie_result(final_description, nutrition['calories'])
        protein = nutrition.get('protein')
        fat = nutrition.get('fat')
        carbs = nutrition.get('carbs')

        # Сохраняем результат
        diary[today] += kcal
        save_user_diary(user_id, diary)

        if today not in food_log:
            food_log[today] = []
        # Сохраняем в формате: [название, калории, белки, жиры, углеводы]
        food_log[today].append([final_description, kcal, protein, fat, carbs])
        save_user_food_log(user_id, food_log)

        # Рассчитываем остаток калорий
        burned = get_user_burned(user_id)
        left_message = get_calories_left_message(profile, diary, burned, today)

        # Формируем сообщение с информацией о питании
        nutrition_parts = [f'{kcal} ккал']
        if protein:
            nutrition_parts.append(f'{protein:.1f}г белка')
        if fat:
            nutrition_parts.append(f'{fat:.1f}г жиров')
        if carbs:
            nutrition_parts.append(f'{carbs:.1f}г углеводов')

        nutrition_text = ', '.join(nutrition_parts)

        await update.message.reply_text(
            f'Блюдо: {final_description}, {nutrition_text}. {left_message}.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Сколько осталось калорий?', callback_data='check_left')]
            ])
        )

    except Exception as e:
        log_detailed_error(e, "при обработке уточнения еды", str(user_id),
                         {"original_description": original_description, "clarification": clarification})
        error_msg = format_error_message(e, "при обработке уточнения",
                                       f'Исходное: "{original_description}", Уточнение: "{clarification}"')
        await update.message.reply_text(error_msg)

    # Сбрасываем флаги
    context.user_data['waiting_for_clarification'] = False
    context.user_data['pending_food_description'] = None
