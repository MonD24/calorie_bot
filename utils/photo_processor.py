# -*- coding: utf-8 -*-
"""
Утилиты для обработки фото еды
"""
import base64
import os
import re
import logging
from typing import Optional, Dict, Any, List

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Блокируем старые методы OpenAI
import openai_safe

from utils.calorie_calculator import ask_gpt, extract_nutrition_smart, validate_calorie_result
from utils.nutrition_validator import validate_nutrition_data, estimate_portion_calories
from data.calorie_database import CALORIE_DATABASE


async def analyze_food_photo(image_base64: str) -> Dict[str, Any]:
    """Анализирует фото еды через GPT Vision"""
    prompt = f"""Определи что за еда на фото и ТОЧНО рассчитай полные БЖУ (белки, жиры, углеводы) и калорийность.

Используй следующие справочные данные:
{CALORIE_DATABASE}

КАЛОРИЙНОСТЬ НА 100г (ЗАПОМНИ!):
- Творог 0%: 70 ккал, 18г белка, 0г жира, 3г углеводов
- Творог 5%: 120 ккал, 17г белка, 5г жира, 2г углеводов  
- Творог 9%: 160 ккал, 16г белка, 9г жира, 2г углеводов
- Банан: 90 ккал, 1.5г белка, 0.3г жира, 23г углеводов
- Арахисовая паста: 600 ккал, 25г белка, 50г жира, 20г углеводов

ВАЖНЫЕ ПРАВИЛА:
1. ВНИМАТЕЛЬНО оцени размер порции относительно посуды/ложки на фото
2. Стандартные порции: столовая ложка ~15г, чайная ~5г, стакан ~200мл
3. ОБЯЗАТЕЛЬНО считай по шагам: сначала каждый ингредиент отдельно, потом сумма
4. ПРОВЕРЯЙ что белки + жиры + углеводы дают правильные калории (белки*4 + жиры*9 + углеводы*4)
5. Если расчет не сходится - пересчитай порции!

ФОРМАТ ОТВЕТА:
ОБЯЗАТЕЛЬНО укажи все 4 показателя в точном формате: "X ккал, Y г белка, Z г жиров, W г углеводов"
Дай краткое описание блюда, затем строго в указанном формате все нутриенты.

Пример: "Творог с кусочками дыни и ложкой варенья. Итого: 280 ккал, 35 г белка, 5 г жиров, 18 г углеводов"

ОБЯЗАТЕЛЬНЫЙ ФОРМАТ РАСЧЕТА:
1. Сначала опиши что видишь и оцени порции каждого ингредиента
2. Посчитай каждый ингредиент: "Творог 9% 150г: 160*1.5 = 240 ккал, 16*1.5 = 24г белка..."  
3. Суммируй: "Всего: X + Y + Z = итого ккал"
4. Проверь: белки*4 + жиры*9 + углеводы*4 = итоговые калории?

ВАЖНО: Даже если жиров или углеводов очень мало, укажи их - НЕ пропускай!

Если нужно уточнение - задай ОДИН вопрос с "ВОПРОС:".
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
        if nutrition['calories'] or nutrition['protein']:
            nutrition = validate_nutrition_data(nutrition, description)
            logging.info(f"После валидации: калории={nutrition['calories']}, белки={nutrition['protein']}, жиры={nutrition['fat']}, углеводы={nutrition['carbs']}")
        
        if nutrition['calories'] and description:
            validated_kcal = validate_calorie_result(description, nutrition['calories'])
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
    description = response.strip()

    # Убираем все что после "Итого:" или "ккал" или развернутые расчеты
    description = re.sub(r'\s*\.?\s*Итого:.*$', '', description, flags=re.IGNORECASE | re.DOTALL)
    description = re.sub(r'\s*\d+\s*ккал.*$', '', description, flags=re.DOTALL)
    description = re.sub(r'\s*\d+\s*$', '', description)

    # Убираем развернутые расчеты (строки с тире и калориями)
    description = re.sub(r'\n\s*-.*$', '', description, flags=re.DOTALL)
    description = re.sub(r'\.\s*-.*$', '', description, flags=re.DOTALL)

    # Убираем переносы строк и лишние пробелы
    description = re.sub(r'\n+', ' ', description)
    description = re.sub(r'\s+', ' ', description)
    description = description.strip()

    if not description or len(description) < 5:
        description = "Блюдо с фото"

    return description


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
