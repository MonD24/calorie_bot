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
from data.calorie_database import CALORIE_DATABASE


async def analyze_food_photo(image_base64: str) -> Dict[str, Any]:
    """Анализирует фото еды через GPT Vision"""
    prompt = f"""Определи что за еда на фото и ТОЧНО рассчитай калорийность и белок.

Используй следующие справочные данные:
{CALORIE_DATABASE}

ВАЖНЫЕ ПРАВИЛА:
1. ВНИМАТЕЛЬНО оцени размер порции относительно посуды/ложки на фото
2. Стандартные порции: столовая ложка ~15г, чайная ~5г, стакан ~200мл
3. Творог 200г = ~160 ккал и 35г белка, дыня 100г = ~35 ккал и 0.6г белка
4. НЕ ЗАВЫШАЙ калорийность! Будь консервативен в оценках
5. Если сомневаешься между двумя значениями - выбирай меньшее

ФОРМАТ ОТВЕТА:
Дай краткое описание блюда, затем укажи калорийность и белок в формате: "X ккал, Y г белка"

Пример: "Творог с кусочками дыни и ложкой варенья. Итого: 280 ккал, 35 г белка"

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
        
        if nutrition['calories'] and description:
            validated_kcal = validate_calorie_result(description, nutrition['calories'])
            result = {
                'description': description,
                'calories': validated_kcal,
                'success': True
            }
            
            # Добавляем белок если найден
            if nutrition['protein'] is not None:
                result['protein'] = round(nutrition['protein'], 1)
            
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
