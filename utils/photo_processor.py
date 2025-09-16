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
    prompt = f"""ПРОАНАЛИЗИРУЙ ФОТО ЕДЫ ПОШАГОВО:

📋 ШАГ 1 - ОПИСАНИЕ БЛЮДА:
Начни ответ с: "На фото [название блюда] - [список всех видимых ингредиентов]"

📊 ШАГ 2 - РАСЧЕТ КАЖДОГО ИНГРЕДИЕНТА:
Используй справочные данные: {CALORIE_DATABASE}

Базовая калорийность на 100г:
• Творог 5%: 120 ккал, 17г белка, 5г жира, 2г углеводов
• Банан: 90 ккал, 1.5г белка, 0.3г жира, 23г углеводов  
• Арахисовая паста: 600 ккал, 25г белка, 50г жира, 20г углеводов

Для каждого ингредиента покажи расчет:
"[Название] ~[вес]г: [калории на 100г]×[коэффициент] = [итого ккал], [белки]г белка, [жиры]г жира, [углеводы]г углеводов"

💯 ШАГ 3 - ИТОГОВАЯ СУММА:
"ИТОГО: [сумма калорий] ккал, [сумма белков] г белка, [сумма жиров] г жиров, [сумма углеводов] г углеводов"

🎯 ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
✅ НАЧНИ с описания: "На фото [блюдо] - [ингредиенты]"
✅ Покажи расчет каждого ингредиента отдельно
✅ Дай итоговую сумму в точном формате
✅ Для сложных блюд результат должен быть 250+ ккал

Пример ответа:
"На фото творог с бананом и арахисовой пастой - творог, кусочки банана, ложка арахисовой пасты.

Творог 5% ~150г: 120×1.5 = 180 ккал, 25.5г белка, 7.5г жира, 3г углеводов
Банан ~80г: 90×0.8 = 72 ккал, 1.2г белка, 0.24г жира, 18.4г углеводов
Арахисовая паста ~20г: 600×0.2 = 120 ккал, 5г белка, 10г жира, 4г углеводов

ИТОГО: 372 ккал, 31.7 г белка, 17.74 г жиров, 25.4 г углеводов"

Если что-то неясно - задай ОДИН вопрос с "ВОПРОС:".
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
    # Ищем строку "На фото..."
    match = re.search(r'На фото (.+?)(?:\n|$|\.|,)', response, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        # Убираем лишние символы в конце
        description = re.sub(r'\s*-\s*.*$', '', description)
        return description
    
    # Если не найдено "На фото", используем старый метод
    description = response.strip()
    
    # Если GPT игнорирует инструкции и сразу пишет калории, возвращаем общее описание
    if re.match(r'^\s*(ШАГ|🔥|Калории|Белок)', response):
        return "Блюдо с фото"

    # Убираем все что после "Итого:" или расчеты
    description = re.sub(r'\s*\.?\s*Итого:.*$', '', description, flags=re.IGNORECASE | re.DOTALL)
    description = re.sub(r'\s*\d+\s*ккал.*$', '', description, flags=re.DOTALL)
    description = re.sub(r'\n.*?~\d+г:.*$', '', description, flags=re.DOTALL)  # убираем расчеты

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
