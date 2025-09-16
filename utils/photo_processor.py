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

КРИТИЧЕСКИ ВАЖНО - АНАЛИЗ ПО ШАГАМ (НЕ ПРОПУСКАЙ НИ ОДНОГО):

ШАГ 1 - ВНИМАТЕЛЬНО ОСМОТРИ ФОТО:
- Что лежит в миске/на тарелке?
- Есть ли что-то СВЕРХУ основного продукта (паста, соус, орехи)?
- Какие цвета видны? Белый творог? Желтые кусочки банана? Коричневая паста?
- Сколько разных текстур и продуктов видно?

ШАГ 2 - ПОЛНЫЙ СПИСОК ИНГРЕДИЕНТОВ:
Перечисли ВСЕ продукты с количествами:
- Основа: творог/каша (~150г обычная порция)
- Фрукты: банан целый (~100г) или кусочки (~50-80г)  
- Добавки: арахисовая паста/мед/орехи (~15-25г видимого количества)

ШАГ 3 - РАСЧЕТ КАЖДОГО ИНГРЕДИЕНТА:
Ингредиент 1: "Творог 5% ~150г: 120×1.5 = 180 ккал, 17×1.5 = 25.5г белка, 5×1.5 = 7.5г жира, 2×1.5 = 3г углеводов"
Ингредиент 2: "Банан ~80г: 90×0.8 = 72 ккал, 1.5×0.8 = 1.2г белка, 0.3×0.8 = 0.24г жира, 23×0.8 = 18.4г углеводов"
Ингредиент 3: "Арахисовая паста ~20г: 600×0.2 = 120 ккал, 25×0.2 = 5г белка, 50×0.2 = 10г жира, 20×0.2 = 4г углеводов"

ШАГ 4 - ИТОГОВАЯ СУММА:
"ИТОГО: 180+72+120 = 372 ккал, 25.5+1.2+5 = 31.7г белка, 7.5+0.24+10 = 17.74г жира, 3+18.4+4 = 25.4г углеводов"

⚠️ ОБЯЗАТЕЛЬНО: Если видишь 2+ ингредиента, итог должен быть 250+ ккал!

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
