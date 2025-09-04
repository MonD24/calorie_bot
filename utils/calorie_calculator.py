# -*- coding: utf-8 -*-
"""
Утилиты для расчета и обработки калорий
"""
import re
import logging
from typing import Optional, Dict, Any

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.calorie_database import CALORIE_DATABASE, LOW_CAL_KEYWORDS, HIGH_CAL_KEYWORDS
from config import VALIDATION_LIMITS, ACTIVITY_MULTIPLIER, GOAL_MULTIPLIERS, OPENAI_API_KEY

# Настройка OpenAI API для новой версии (1.0+)
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
    logging.info("OpenAI client инициализирован (новая версия)")
except ImportError:
    OPENAI_AVAILABLE = False
    client = None
    logging.warning("OpenAI library not available. GPT features will be disabled.")


def calculate_bmr_tdee(weight: float, height: float, age: int, sex: str, goal: str = 'deficit') -> Dict[str, Any]:
    """
    Рассчитывает BMR, TDEE и целевые калории по формуле Миффлина-Сан Жеора
    """
    # Формула Миффлина — Сан Жеора
    if sex == 'муж':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # жен
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Учитываем коэффициент активности
    tdee = int(bmr * ACTIVITY_MULTIPLIER)
    
    # Рассчитываем целевые калории в зависимости от цели
    target = int(tdee * GOAL_MULTIPLIERS.get(goal, 1.0))
    
    return {
        'bmr': int(bmr),
        'tdee': tdee,
        'target': target,
        'goal': goal
    }


def create_calorie_prompt(description: str, is_clarification: bool = False) -> str:
    """Создает улучшенный промпт для определения калорий"""
    base_prompt = f"""
Рассчитай калорийность блюда: "{description}"

Используй следующие справочные данные:
{CALORIE_DATABASE}

ПРАВИЛА РАСЧЕТА:
1. Оценивай реальные порции: стандартная тарелка ~200-300г, столовая ложка ~15г, чайная ~5г
2. Учитывай способ приготовления: жареное +20-30% калорий, вареное без изменений
3. Если не указан вес, используй стандартные порции взрослого человека
4. При сомнениях в размере порции, бери средние значения

"""
    
    if is_clarification:
        base_prompt += "ВАЖНО: Информации достаточно для расчета. Ответь ТОЛЬКО числом калорий без дробей."
    else:
        base_prompt += """
Если информации достаточно для точного расчета - ответь ТОЛЬКО числом калорий без дробей.
Если нужны критически важные уточнения (размер порции, способ приготовления), задай ОДИН конкретный вопрос и добавь "ВОПРОС:".
"""
    
    return base_prompt


def validate_calorie_result(description: str, kcal: int) -> int:
    """Валидация результата расчета калорий"""
    description_lower = description.lower()
    
    # Проверяем на разумность результата
    min_cal = VALIDATION_LIMITS['calories']['min']
    max_cal = VALIDATION_LIMITS['calories']['max']
    
    if kcal < min_cal:
        logging.warning(f"Very low calories ({kcal}) for '{description}' - adjusting to {min_cal}")
        return min_cal
    
    if kcal > max_cal:
        logging.warning(f"Very high calories ({kcal}) for '{description}' - might be incorrect")
        # Для очень калорийных блюд оставляем как есть, но логируем
    
    # Быстрые проверки на основе ключевых слов
    has_low_cal = any(word in description_lower for word in LOW_CAL_KEYWORDS)
    has_high_cal = any(word in description_lower for word in HIGH_CAL_KEYWORDS)
    
    if has_low_cal and kcal > 500:
        adjusted = min(kcal, 300)
        logging.info(f"Adjusting high calories for low-cal food: {description} ({kcal} -> {adjusted})")
        return adjusted
    
    if has_high_cal and kcal < 200:
        adjusted = max(kcal, 250)
        logging.info(f"Adjusting low calories for high-cal food: {description} ({kcal} -> {adjusted})")
        return adjusted
    
    return kcal


def extract_calories_smart(response_text: str) -> Optional[int]:
    """Умное извлечение калорий из ответа GPT"""
    response_text = response_text.strip()
    logging.info(f"Extracting calories from: {response_text}")
    
    # Если это просто число
    if response_text.replace('.', '').replace(',', '').isdigit():
        return int(float(response_text.replace(',', '.')))
    
    # Ищем число после ключевых слов
    patterns = [
        r'итого:?\s*(\d+)',
        r'всего:?\s*(\d+)', 
        r'общая\s+калорийность:?\s*(\d+)', 
        r'калорийность:?\s*(\d+)', 
        r'(\d+)\s*ккал',
        r'=\s*(\d+)',
        r'составляет?\s*(\d+)',
        r'примерно\s*(\d+)',
        r'около\s*(\d+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            # Берем последнее найденное значение (обычно итоговое)
            result = int(matches[-1])
            logging.info(f"Found calories using pattern '{pattern}': {result}")
            return result
    
    # Если ничего не нашли в паттернах, берем все числа
    numbers = [int(x) for x in re.findall(r'\d+', response_text) if int(x) > 10]
    if numbers:
        # Выбираем наиболее вероятное итоговое значение
        result = max(numbers) if len(numbers) == 1 else numbers[-1]
        logging.info(f"Using fallback number extraction: {result}")
        return result
    
    logging.warning(f"Could not extract calories from: {response_text}")
    return None


async def ask_gpt(messages: list) -> str:
    """Отправляет запрос к OpenAI GPT"""
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI library not available")
    
    try:
        # Используем только новую версия OpenAI API (1.0+)
        if 'client' not in globals() or client is None:
            raise Exception("OpenAI client not initialized")
            
        # Определяем модель: используем gpt-4o для vision задач, gpt-4o-mini для текста
        has_image = any(
            isinstance(msg.get('content'), list) and 
            any(item.get('type') == 'image_url' for item in msg.get('content', []))
            for msg in messages
        )
        model = "gpt-4o" if has_image else "gpt-4o-mini"
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        raise


def get_calories_left_message(profile: Dict[str, Any], diary: Dict[str, int], 
                             burned: Dict[str, int], today: str) -> str:
    """
    Универсальная функция для расчёта оставшихся калорий
    """
    target_calories = profile.get('target_calories')
    old_target_limit = profile.get('target_limit')  # Совместимость со старыми профилями
    goal = profile.get('goal', 'deficit')
    
    eaten_today = diary.get(today, 0)
    burned_today = burned.get(today, 0)
    
    if target_calories:
        # Новая система с автоматическим расчётом
        left = target_calories - eaten_today
        
        goal_names = {
            'deficit': 'до цели похудения',
            'maintain': 'до поддержания веса',
            'surplus': 'до цели набора массы'
        }
        goal_name = goal_names.get(goal, 'до цели')
        
        if left > 0:
            left_message = f"Осталось {goal_name}: {left} ккал"
            if burned_today > 0:
                left_message += f" (+ {burned_today} ккал за активность)"
        else:
            left_message = f"Превышение {goal_name.replace('до ', '')}: {abs(left)} ккал"
            
    elif old_target_limit:
        # Старая система с ручным лимитом (для совместимости)
        net_calories = eaten_today - burned_today
        left = old_target_limit - net_calories
        left_message = f"Осталось до лимита: {max(left, 0)} ккал"
        if left < 0:
            left_message += f" (превышение на {abs(left)} ккал)"
    else:
        # Если ничего не настроено
        norm = profile.get('norm', 0)
        
        if not norm:
            # Профиль не настроен
            return f"📝 Съедено: {eaten_today} ккал\n\n⚠️ Установите цель командой /goal для расчёта остатка калорий."
        
        left = norm - eaten_today
        if left > 0:
            left_message = f"Осталось на сегодня: {left} ккал"
            if burned_today > 0:
                left_message += f" (+ {burned_today} ккал за активность)"
        else:
            left_message = f"Превышение дневной нормы: {abs(left)} ккал"
    
    return left_message
