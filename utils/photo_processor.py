# -*- coding: utf-8 -*-
"""
Утилиты для обработки фото еды
"""
import re
import logging
from typing import Optional, Dict, Any, List

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.calorie_calculator import ask_gpt, extract_nutrition_smart, validate_calorie_result
from utils.nutrition_validator import validate_nutrition_data
from data.calorie_database import CALORIE_DATABASE


async def analyze_food_photo(image_base64: str) -> Dict[str, Any]:
    """Анализирует фото еды через GPT Vision"""
    prompt = f"""ВНИМАТЕЛЬНО ПРОАНАЛИЗИРУЙ ФОТО ЕДЫ И РАССЧИТАЙ КАЛОРИЙНОСТЬ ПОШАГОВО:

📋 ШАГ 1 - ДЕТАЛЬНОЕ ОПИСАНИЕ:
Начни ответ СТРОГО с: "На фото [название основного блюда]: [ингредиент 1], [ингредиент 2], [ингредиент 3] и т.д."

ПРИМЕР ПРАВИЛЬНОГО ОПИСАНИЯ:
"На фото куриное блюдо с гарниром: жареная куриная грудка, отварной рис, вареное яйцо, маринованные огурцы, болгарский перец"

ВАЖНО: Перечисли через запятую ВСЕ видимые продукты на тарелке!

📊 ШАГ 2 - РАСЧЕТ КАЖДОГО ИНГРЕДИЕНТА:
Используй справочные данные: {CALORIE_DATABASE}

КРИТИЧЕСКИ ВАЖНО:
• Куриная грудка: 165 ккал/100г, 31г белка, 3.6г жира
• Рис/булгур вареный: 116 ккал/100г, 2.2г белка, 0.5г жира, 23г углеводов
• Яйцо вареное: 155 ккал/100г (1 целое яйцо ~70 ккал)
• Огурцы маринованные: 16 ккал/100г, 0.8г белка

Для каждого ингредиента покажи расчет:
"[Название] ~[реальный_вес]г: [калории на 100г] × [коэффициент] = [итого ккал], [белки]г белка, [жиры]г жира, [углеводы]г углеводов"

ОЦЕНКА ВЕСА ПО ФОТО:
• Куриная грудка в тарелке: обычно 100-150г
• Порция гарнира (рис/булгур): 100-150г
• Вареное яйцо: 1 штука = 50г
• Маринованные огурцы: 3-4 штуки = 60-80г

💯 ШАГ 3 - ИТОГОВАЯ СУММА:
"ИТОГО: [сумма калорий] ккал, [сумма белков] г белка, [сумма жиров] г жиров, [сумма углеводов] г углеводов"

🎯 ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
✅ ВНИМАТЕЛЬНО рассмотри ВСЕ ингредиенты на тарелке
✅ Используй реалистичные порции для взрослого человека
✅ Для блюда из нескольких ингредиентов результат должен быть 300+ ккал
✅ НЕ недооценивай количество продуктов!

Пример для сложного блюда:
"На фото куриная грудка с рисом и овощами - кусочки жареной курицы, порция отварного риса, вареное яйцо, маринованные огурцы.

Куриная грудка жареная ~120г: 165×1.2×1.2 = 238 ккал, 37г белка, 5г жиров, 0г углеводов
Рис отварной ~100г: 116×1.0 = 116 ккал, 2.2г белка, 0.5г жиров, 23г углеводов
Яйцо вареное ~50г: 155×0.5 = 78 ккал, 6.5г белка, 5.5г жиров, 0.4г углеводов
Огурцы маринованные ~60г: 16×0.6 = 10 ккал, 0.5г белка, 0г жиров, 2г углеводов

ИТОГО: 442 ккал, 46.2 г белка, 11 г жиров, 25.4 г углеводов"

Если что-то неясно - задай ОДИН конкретный вопрос с "ВОПРОС:".
"""

    messages = [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}}
        ]
    }]

    try:
        response = await ask_gpt(messages)
        logging.info(f"GPT photo analysis response: {response}")

        # Проверяем на отказ GPT
        refusal_phrases = ['извините', 'не могу', 'невозможно', 'не в состоянии']
        if any(phrase in response.lower() for phrase in refusal_phrases):
            return {'error': 'GPT не может проанализировать фото'}

        # Проверяем, задал ли GPT вопрос
        if "ВОПРОС:" in response:
            question = response.replace("ВОПРОС:", "").strip()
            return {'question': question}

        # Извлекаем калории, белок и описание
        nutrition = extract_nutrition_smart(response)
        description = extract_description_from_photo_response(response)

        # Логируем извлеченные данные
        logging.info(f"Извлечено: калории={nutrition['calories']}, белки={nutrition['protein']}, жиры={nutrition['fat']}, углеводы={nutrition['carbs']}")

        # Валидируем данные
        logging.info(f"🔍 НАЧАЛО ВАЛИДАЦИИ для '{description}'")
        logging.info(f"🔍 Исходные данные: {nutrition}")

        if nutrition['calories'] or nutrition['protein']:
            nutrition = validate_nutrition_data(nutrition, description)
            logging.info(f"🔍 После валидации: {nutrition}")

        if nutrition['calories'] and description:
            validated_kcal = validate_calorie_result(description, nutrition['calories'])
            logging.info(f"🔍 Финальная калорийность: {nutrition['calories']} -> {validated_kcal}")
            result = {
                'description': description,
                'calories': validated_kcal,
                'success': True
            }

            # Добавляем все БЖУ если найдены
            if nutrition['protein'] is not None:
                result['protein'] = round(nutrition['protein'], 1)
            if nutrition['fat'] is not None:
                result['fat'] = round(nutrition['fat'], 1)
            if nutrition['carbs'] is not None:
                result['carbs'] = round(nutrition['carbs'], 1)

            return result
        else:
            return {'error': 'Не удалось извлечь калории или описание из ответа'}

    except Exception as e:
        logging.error(f"Error analyzing photo: {e}")
        return {'error': f'Ошибка анализа фото: {str(e)}'}


def extract_calories_from_photo_response(response: str) -> Optional[int]:
    """Извлекает калории из ответа GPT по фото"""
    # Сначала пробуем найти число после слов "итого", "всего", "общая калорийность"
    total_match = re.search(r'(?:итого|всего|общая калорийность)[^0-9]*(\d+)', response, re.IGNORECASE)
    if total_match:
        return int(total_match.group(1))

    # Если не нашли "итого", берем все числа и выбираем наибольшее
    numbers = [int(x) for x in re.findall(r'\d+', response)]
    if numbers:
        return max(numbers)  # Берем максимальное число как итоговую калорийность

    return None


def extract_description_from_photo_response(response: str) -> str:
    """Извлекает описание блюда из ответа GPT"""
    # Ищем строку "На фото..." до первого ШАГа, расчётов или технических символов
    match = re.search(r'На фото (.+?)(?=\n\n|📊|ШАГ|~\d+г:|ИТОГО:|Расчет|$)', response, re.IGNORECASE | re.DOTALL)
    if match:
        description = match.group(1).strip()
        # Убираем технические символы и лишний текст в конце
        description = re.sub(r'📊.*$', '', description)  # убираем все после 📊
        description = re.sub(r'\s*Расчет.*$', '', description)  # убираем "Расчет калорий.."
        description = re.sub(r'\.$', '', description)  # убираем точку в конце
        # Очищаем от лишних переносов, но сохраняем структуру
        description = re.sub(r'\s+', ' ', description)
        return description.strip()

    # Альтернативный поиск - ищем полное описание в первых строках
    lines = response.split('\n')
    description_lines = []

    for i, line in enumerate(lines):
        line = line.strip()
        # Пропускаем пустые строки и технические символы в начале
        if not line or line.startswith(('📋', '📊', '💯', '🎯')):
            continue
        # Останавливаемся на расчётах или шагах
        if any(keyword in line for keyword in ['ШАГ', '~', 'г:', 'ИТОГО', '165×', '116×', 'Расчет']):
            break
        # Собираем строки описания
        if len(line) > 5:
            description_lines.append(line)

    if description_lines:
        full_description = ' '.join(description_lines)
        # Убираем технические символы
        full_description = re.sub(r'^[📋📊💯🎯\-\s]*', '', full_description)
        # Убираем лишний текст в конце
        full_description = re.sub(r'📊.*$', '', full_description)
        full_description = re.sub(r'\s*Расчет.*$', '', full_description)
        return full_description.strip()

    # Если ничего не найдено, возвращаем общее описание
    return "Блюдо с фото"


def extract_ingredients_from_description(description: str) -> List[str]:
    """Извлекает ингредиенты из описания блюда"""
    # Убираем базовое слово (творог, салат и т.д.) и извлекаем ингредиенты после "с"
    if ' с ' in description:
        parts = description.split(' с ', 1)
        if len(parts) > 1:
            ingredients_part = parts[1]
            # Разбиваем по запятым и союзам
            ingredients = re.split(r',|\s+и\s+', ingredients_part)
            return [ing.strip() for ing in ingredients if ing.strip()]

    return []


def get_base_dish_from_description(description: str) -> str:
    """Извлекает базовое блюдо из описания"""
    if ' с ' in description:
        return description.split(' с ')[0].strip()
    return description.strip()
