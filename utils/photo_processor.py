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
    prompt = f"""Проанализируй фото еды и рассчитай калорийность.

⚠️ ВАЖНО: 
- Если на фото НЕСКОЛЬКО блюд - посчитай КАЖДОЕ ОТДЕЛЬНО
- Игнорируй посторонние предметы (таблетки, салфетки). Анализируй ТОЛЬКО ЕДУ

📋 ФОРМАТ ОТВЕТА:

Если НЕСКОЛЬКО блюд:
На фото:
1. [Название блюда 1] ~[вес]г - [ккал] ккал, [Б]г белка, [Ж]г жира, [У]г углеводов
2. [Название блюда 2] ~[вес]г - [ккал] ккал, [Б]г белка, [Ж]г жира, [У]г углеводов

ИТОГО: [сумма ккал] ккал, [сумма Б]г белка, [сумма Ж]г жира, [сумма У]г углеводов

Если ОДНО блюдо:
На фото [название блюда] ~[вес]г

ИТОГО: [ккал] ккал, [Б]г белка, [Ж]г жира, [У]г углеводов

📊 СПРАВОЧНИК КАЛОРИЙНОСТИ (на 100г):
{CALORIE_DATABASE}

🔴 ДОПОЛНИТЕЛЬНО:
• Макароны вареные: 112 ккал, 3.5г Б, 0.4г Ж, 23г У
• Котлета мясная жареная: 250 ккал, 17г Б, 18г Ж, 5г У  
• Салат с майонезом: 180-220 ккал, 5г Б, 15г Ж, 8г У
• Пиво 500мл: 210 ккал, 1.5г Б, 0г Ж, 17г У

⚠️ ТИПИЧНЫЕ ПОРЦИИ:
• Тарелка салата: 200-300г
• Порция гарнира: 150-200г
• Котлета: 80-100г (2 шт = 160-200г)
• Бокал пива: 500мл

🚨 ОБЯЗАТЕЛЬНО укажи ИТОГО с ПОЛНЫМИ БЖУ в формате:
ИТОГО: XXX ккал, XXг белка, XXг жира, XXг углеводов

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

        # Проверяем на отказ GPT (только если явный отказ без расчетов)
        refusal_phrases = ['извините', 'не могу', 'невозможно', 'не в состоянии']
        has_refusal = any(phrase in response.lower() for phrase in refusal_phrases)
        has_calculations = 'ккал' in response.lower() or 'калор' in response.lower()
        
        # Возвращаем ошибку только если есть отказ И нет расчетов
        if has_refusal and not has_calculations:
            logging.warning(f"GPT refused to analyze photo: {response[:200]}")
            return {'error': 'GPT не может проанализировать фото'}

        # Проверяем, задал ли GPT вопрос
        if "ВОПРОС:" in response:
            question = response.replace("ВОПРОС:", "").strip()
            return {'question': question}

        # Извлекаем калории, белок и описание
        nutrition = extract_nutrition_smart(response)
        description = extract_description_from_photo_response(response)

        # Логируем извлеченные данные
        logging.info(f"📊 Извлечено из GPT: калории={nutrition['calories']}, белки={nutrition['protein']}, жиры={nutrition['fat']}, углеводы={nutrition['carbs']}")
        logging.info(f"📝 Описание: {description}")

        # Если не удалось извлечь калории, но есть текст - пробуем альтернативные методы
        if not nutrition['calories'] and response:
            logging.warning(f"❌ Не удалось извлечь калории стандартным способом. Полный ответ GPT:\n{response}")
            # Пробуем найти ИТОГО вручную
            itogo_match = re.search(r'ИТОГО[:\s]+(\d+)\s*ккал', response, re.IGNORECASE)
            if itogo_match:
                nutrition['calories'] = int(itogo_match.group(1))
                logging.info(f"✅ Нашли калории через ИТОГО: {nutrition['calories']}")

        # Валидируем данные
        logging.info(f"🔍 НАЧАЛО ВАЛИДАЦИИ для '{description}'")
        logging.info(f"🔍 Исходные данные: {nutrition}")

        if nutrition['calories'] or nutrition['protein']:
            nutrition = validate_nutrition_data(nutrition, description)
            logging.info(f"🔍 После валидации: {nutrition}")

        if nutrition['calories'] and description:
            # validate_nutrition_data уже проверил и исправил калории на основе БЖУ
            # Дополнительная валидация НЕ нужна, она может испортить правильное значение
            logging.info(f"🔍 Финальная калорийность: {nutrition['calories']} ккал")
            result = {
                'description': description,
                'calories': nutrition['calories'],  # Используем откалиброванное значение
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
            logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось извлечь данные.\nОтвет GPT:\n{response}")
            return {
                'error': 'Не удалось распознать блюдо. Попробуйте описать его текстом.',
                'debug_response': response[:500]  # Для отладки
            }

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
    
    # Сначала пробуем найти описание в формате "На фото: 1. Блюдо1 ... 2. Блюдо2 ..."
    # Формат GPT: "На фото:\n1. Греческий салат ~350г - 806 ккал...\n2. Бокал пива ~500мл - 210 ккал..."
    
    # Ищем блюда в формате "1. Название" или "1) Название" в начале строки
    dish_pattern = r'^(\d)[.)]\s*([А-Яа-яЁёA-Za-z][^-\n]+?)(?:\s*[-~]|\s*$)'
    dish_matches = re.findall(dish_pattern, response, re.MULTILINE)
    
    if len(dish_matches) >= 2:
        # Нашли несколько блюд
        dishes = []
        for num, desc in dish_matches[:3]:  # Максимум 3 блюда
            desc = desc.strip()
            # Очищаем от технических символов и веса
            desc = re.sub(r'\s*~?\d+\s*[гgмлml]+\s*$', '', desc)  # убираем "~350г" или "~500мл" в конце
            desc = re.sub(r'[📊💯🧮\*]+.*$', '', desc)
            # Упрощаем описание - если формат "Категория: название", берём название
            if ':' in desc:
                parts = desc.split(':', 1)
                category = parts[0].strip().lower()
                details = parts[1].strip() if len(parts) > 1 else ''
                # Если категория общая (напиток, блюдо и т.д.), используем детали
                generic_categories = ['напиток', 'блюдо', 'еда', 'продукт']
                if category in generic_categories and details:
                    desc = details.rstrip('.').capitalize()
                elif category == 'салат' and details:
                    # Для салата: если детали короткие - добавляем, иначе просто "Салат"
                    if len(details) < 25:
                        desc = f"Салат ({details.rstrip('.')})"
                    else:
                        desc = "Салат"
                elif details and len(details) < 25:
                    # Для других: если детали короткие - добавляем
                    desc = f"{parts[0].strip()} ({details.rstrip('.')})"
                else:
                    desc = parts[0].strip()
            desc = desc.strip()
            if desc and len(desc) > 2:
                dishes.append(desc)
        
        if len(dishes) >= 2:
            # Красивый формат для нескольких блюд
            result = "\n".join([f"  • {d}" for d in dishes])
            return result
        elif dishes:
            return dishes[0]
    
    # Проверяем на явное указание нескольких блюд
    multiple_dishes_match = re.search(r'На фото (два|три|2|3|несколько) блюд[а-я]*', response, re.IGNORECASE)
    
    if multiple_dishes_match or 'БЛЮДО 1:' in response.upper():
        # Пробуем найти блюда по формату "БЛЮДО 1: Название"
        dish_patterns = [
            r'БЛЮДО\s*1[:\s]+([А-Яа-яЁё][^.\n]+)',
            r'БЛЮДО\s*2[:\s]+([А-Яа-яЁё][^.\n]+)',
        ]
        
        dishes = []
        for pattern in dish_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                dish_desc = match.group(1).strip()
                dish_desc = re.sub(r'[📊💯🧮\*]+.*$', '', dish_desc)
                dish_desc = re.sub(r'\s+', ' ', dish_desc).strip()
                if dish_desc and len(dish_desc) > 3:
                    dishes.append(dish_desc)
        
        if len(dishes) >= 2:
            return "\n".join([f"  • {d}" for d in dishes])
        elif dishes:
            return dishes[0]
    
    # Ищем строку "На фото..." до первого расчёта
    match = re.search(r'На фото[:\s]+(.+?)(?=\n\n|📊|ШАГ|~\d+г:|ИТОГО:|Расчет|\d+\s*ккал|$)', response, re.IGNORECASE | re.DOTALL)
    if match:
        description = match.group(1).strip()
        # Убираем технические символы и лишний текст
        description = re.sub(r'📊.*$', '', description)
        description = re.sub(r'\s*Расчет.*$', '', description)
        description = re.sub(r'\s*~?\d+\s*[гgмлml]+\s*$', '', description)  # убираем вес в конце
        description = re.sub(r'\.$', '', description)
        description = re.sub(r'\s+', ' ', description)
        
        # Если описание содержит нумерованный список, извлекаем названия блюд
        if re.search(r'\d[.)]\s', description):
            parts = re.findall(r'\d[.)]\s*([А-Яа-яЁёA-Za-z][^,;\d]+)', description)
            if parts:
                clean_parts = []
                for p in parts[:3]:
                    p = re.sub(r'\s*[-~].*$', '', p).strip()
                    if p and len(p) > 2:
                        clean_parts.append(p)
                if len(clean_parts) >= 2:
                    return "\n".join([f"  • {p}" for p in clean_parts])
                elif clean_parts:
                    return clean_parts[0]
        
        if description and len(description) > 3:
            return description.strip()

    # Альтернативный поиск - ищем полное описание в первых строках
    lines = response.split('\n')
    description_lines = []

    for i, line in enumerate(lines):
        line = line.strip()
        # Пропускаем пустые строки и технические символы
        if not line or line.startswith(('📋', '📊', '💯', '🎯')):
            continue
        # Останавливаемся на расчётах
        if any(keyword in line for keyword in ['ШАГ', 'ИТОГО', 'Расчет', 'ккал', 'белка', 'жир']):
            break
        # Собираем строки описания (только текстовые, не с цифрами расчётов)
        if len(line) > 5 and not re.match(r'^[\d~×=\-\+]', line):
            description_lines.append(line)
        # Ограничиваем количество строк
        if len(description_lines) >= 3:
            break

    if description_lines:
        full_description = ' '.join(description_lines)
        full_description = re.sub(r'^[📋📊💯🎯\-\s]*', '', full_description)
        full_description = re.sub(r'📊.*$', '', full_description)
        full_description = re.sub(r'\s*Расчет.*$', '', full_description)
        full_description = re.sub(r'\s*~?\d+\s*[гgмлml]+\s*$', '', full_description)  # убираем вес
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
