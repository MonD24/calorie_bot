# -*- coding: utf-8 -*-
"""
Утилиты для расчета и обработки калорий
"""
import re
import logging
from typing import Optional, Dict, Any
import datetime

# Исправляем импорты для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Блокируем старые методы OpenAI
import openai_safe

from data.calorie_database import CALORIE_DATABASE, LOW_CAL_KEYWORDS, HIGH_CAL_KEYWORDS
from config import VALIDATION_LIMITS, ACTIVITY_MULTIPLIER, GOAL_MULTIPLIERS, OPENAI_API_KEY
from .user_data import get_user_profile, get_user_food_log

# Настройка OpenAI API - только новая версия (1.0+)
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
    logging.info("OpenAI client инициализирован (безопасная версия)")
except ImportError:
    OPENAI_AVAILABLE = False
    client = None
    logging.warning("OpenAI library not available. GPT features will be disabled.")
except Exception as e:
    OPENAI_AVAILABLE = False
    client = None
    logging.error(f"Ошибка инициализации OpenAI: {e}")


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
    """Создает улучшенный промпт для определения калорий и белка"""
    base_prompt = f"""
Рассчитай калорийность и белок блюда: "{description}"

Используй следующие справочные данные:
{CALORIE_DATABASE}

ПРАВИЛА РАСЧЕТА:
1. Оценивай реальные порции: стандартная тарелка ~200-300г, столовая ложка ~15г, чайная ~5г
2. Учитывай способ приготовления: жареное +20-30% калорий, вареное без изменений
3. Если не указан вес, используй стандартные порции взрослого человека
4. При сомнениях в размере порции, бери средние значения

РАСПОЗНАВАНИЕ ЖАРЕНЫХ ИЗДЕЛИЙ:
- Если видишь золотистое полукруглое жареное изделие - это ЧЕБУРЕК (120г = 300 ккал)
- Сразу давай точный расчет: "Это чебурек. 300 ккал, 10г белка, 15г жиров, 25г углеводов"
- НЕ спрашивай про начинку и вес - используй стандартные значения

ОСОБОЕ ВНИМАНИЕ К ВЫСОКОКАЛОРИЙНЫМ ПРОДУКТАМ:
- Арахисовая паста: 588 ккал/100г (1 ст.л. = ~15г = ~90 ккал)
- Масла: 750+ ккал/100г (1 ст.л. = ~15г = ~115 ккал)
- Орехи: 550-650 ккал/100г
- Сыры: 300-400 ккал/100г
- Не недооценивай количество этих продуктов на фото!

РАСПОЗНАВАНИЕ ПОПУЛЯРНЫХ БЛЮД:
- ШАУРМА: обычно в лаваше с мясом, овощами, соусом. Средняя порция 300-400г = 750-1200 ккал
- Если видишь лаваш с начинкой или завернутое блюдо в фольге - скорее всего шаурма
- ЧЕБУРЕК: жареный полукруглый пирожок золотистого цвета с хрустящим тестом
- Если видишь золотистое жареное изделие полукруглой формы - это чебурек (средний 120г = 300 ккал)
- БЕЛЯШ: круглый жареный пирожок с открытой серединкой
- ПИРОЖОК ЖАРЕНЫЙ: любой жареный пирожок золотистого цвета
- ПИЦЦА: треугольный кусок = ~1/8 пиццы (~150г), целая пицца = ~1200г
- БУРГЕРЫ: стандартный = 200-250г, большой = 300-400г
- РОЛЛЫ/СУШИ: 1 ролл = 20-30г, порция обычно 6-8 роллов

"""

    if is_clarification:
        base_prompt += "ВАЖНО: Информации достаточно для расчета. Ответь в формате: X ккал, Y г белка, Z г жиров, W г углеводов"
    else:
        base_prompt += """
Если информации достаточно для точного расчета - ответь в формате: X ккал, Y г белка, Z г жиров, W г углеводов
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

    # НОВАЯ ПРОВЕРКА: Специфичные высококалорийные продукты
    high_cal_products = ['арахисовая паста', 'нутелла', 'масло', 'орехи', 'сыр']
    has_very_high_cal = any(product in description_lower for product in high_cal_products)

    if has_low_cal and kcal > 500:
        adjusted = min(kcal, 300)
        logging.info(f"Adjusting high calories for low-cal food: {description} ({kcal} -> {adjusted})")
        return adjusted

    if has_high_cal and kcal < 200:
        adjusted = max(kcal, 250)
        logging.info(f"Adjusting low calories for high-cal food: {description} ({kcal} -> {adjusted})")
        return adjusted

    # НОВАЯ ЛОГИКА: Проверка блюд с арахисовой пастой и другими очень калорийными продуктами
    if has_very_high_cal and kcal < 300:
        adjusted = max(kcal, 350)  # Минимум 350 ккал для блюд с арахисовой пастой
        logging.info(f"Adjusting low calories for very high-cal product: {description} ({kcal} -> {adjusted})")
        return adjusted

    return kcal


def extract_calories_smart(response_text: str) -> Optional[int]:
    """Умное извлечение калорий из ответа GPT"""
    response_text = response_text.strip()
    logging.info(f"Extracting calories from: {response_text}")

    # Если это просто число
    if response_text.replace('.', '').replace(',', '').isdigit():
        return int(float(response_text.replace(',', '.')))

    # Ищем число после ключевых слов (в порядке приоритета)
    patterns = [
        r'итого:?\s*(\d+(?:[.,]\d+)?)\s*ккал',  # итого: 450 ккал
        r'всего\s+(\d+(?:[.,]\d+)?)\s*ккал',  # всего 450 ккал
        r'итого:?\s*(\d+(?:[.,]\d+)?)',  # итого: 450
        r'всего:?\s*(\d+(?:[.,]\d+)?)',  # всего: 450
        r'общая\s+калорийность:?\s*(\d+(?:[.,]\d+)?)',
        r'калорийность:?\s*(\d+(?:[.,]\d+)?)',
        r'калории:?\s*(\d+(?:[.,]\d+)?)',  # калории: 450
        r'(\d+(?:[.,]\d+)?)\s*ккал',  # 450 ккал
        r'(\d+(?:[.,]\d+)?)\s*калори[йяе]',  # 450 калорий
        r'=\s*(\d+(?:[.,]\d+)?)',
        r'составляет?\s*(\d+(?:[.,]\d+)?)',
        r'примерно\s*(\d+(?:[.,]\d+)?)',
        r'около\s*(\d+(?:[.,]\d+)?)'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            # Берем последнее найденное значение (обычно итоговое)
            result = int(float(matches[-1].replace(',', '.')))
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


def extract_protein_smart(response_text: str) -> Optional[float]:
    """Умное извлечение белка из ответа GPT"""
    response_text = response_text.strip()
    logging.info(f"Extracting protein from: {response_text[:200]}")

    # Ищем белок в различных форматах (от более специфичных к менее специфичным)
    patterns = [
        r'белки:?\s*(\d+(?:[.,]\d+)?)\s*г',  # белки: 30г или Белки: 30 г
        r'белок[а-я]*:?\s*(\d+(?:[.,]\d+)?)\s*г',
        r'(\d+(?:[.,]\d+)?)\s*г\s*белка',
        r'(\d+(?:[.,]\d+)?)\s*г\s*белк',
        r'белк[а-я]*\s*(\d+(?:[.,]\d+)?)\s*г',  # более строгий паттерн
        r'(\d+(?:[.,]\d+)?)\s*грамм\s*белка',  # 25 грамм белка
        r'(?:^|[,.\s])\s*б:?\s*(\d+(?:[.,]\d+)?)\s*г',  # б: 35г (с началом строки или разделителем)
        r'protein:?\s*(\d+(?:[.,]\d+)?)',
        r'(\d+(?:[.,]\d+)?)\s*g\s*protein'
    ]

    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            all_matches.extend([(float(m.replace(',', '.')), pattern) for m in matches])

    if all_matches:
        # Берем ПОСЛЕДНЕЕ найденное значение (обычно это итоговое)
        result, pattern = all_matches[-1]
        logging.info(f"Found protein using pattern '{pattern}': {result}г (из {len(all_matches)} найденных)")
        return result

    logging.warning(f"Could not extract protein from: {response_text[:200]}")
    return None


def extract_fat_smart(response_text: str) -> Optional[float]:
    """Умное извлечение жиров из ответа GPT"""
    if not response_text:
        logging.info("📊 ЖИРЫ: Пустой текст")
        return None

    logging.info(f"📊 ЖИРЫ: Поиск в тексте длиной {len(response_text)}")

    # Ищем жиры в различных форматах (от более специфичных к менее специфичным)
    patterns = [
        r'жиры:?\s*(\d+(?:[.,]\d+)?)\s*г',  # жиры: 18г или Жиры: 18 г
        r'жир[а-я]*:?\s*(\d+(?:[.,]\d+)?)\s*г',
        r'(\d+(?:[.,]\d+)?)\s*г\s*жиров?',  # 18 г жиров
        r'жир[а-я]*\s*(\d+(?:[.,]\d+)?)\s*г',  # жиры 18 г
        r'жирность\s*(\d+(?:[.,]\d+)?)\s*грамм',  # жирность 10 грамм
        r'(?:^|[,.\s])\s*ж:?\s*(\d+(?:[.,]\d+)?)\s*г',  # ж: 16г (с началом строки или разделителем)
        r'fat:?\s*(\d+(?:[.,]\d+)?)',
        r'(\d+(?:[.,]\d+)?)\s*g\s*fat',
        r'липид[а-я]*:?\s*(\d+(?:[.,]\d+)?)'
    ]

    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            all_matches.extend([(float(m.replace(',', '.')), pattern) for m in matches])

    if all_matches:
        # Берем ПОСЛЕДНЕЕ найденное значение (обычно это итоговое)
        result, pattern = all_matches[-1]
        logging.info(f"📊 ЖИРЫ: Найдено {result}г по паттерну '{pattern}' (из {len(all_matches)} найденных)")
        return result

    logging.warning(f"📊 ЖИРЫ: НЕ НАЙДЕНО в тексте")
    return None


def extract_carbs_smart(response_text: str) -> Optional[float]:
    """Умное извлечение углеводов из ответа GPT"""
    if not response_text:
        logging.info("📊 УГЛЕВОДЫ: Пустой текст")
        return None

    logging.info(f"📊 УГЛЕВОДЫ: Поиск в тексте длиной {len(response_text)}")

    # Ищем углеводы в различных форматах (от более специфичных к менее специфичным)
    patterns = [
        r'углеводы:?\s*(\d+(?:[.,]\d+)?)\s*г',  # углеводы: 6г или Углеводы: 6 г
        r'углевод[а-я]*:?\s*(\d+(?:[.,]\d+)?)\s*г',
        r'(\d+(?:[.,]\d+)?)\s*г\s*углеводов?',  # 6 г углеводов
        r'углевод[а-я]*\s*(\d+(?:[.,]\d+)?)\s*г',  # углеводы 6 г
        r'углеводов\s*(\d+(?:[.,]\d+)?)\s*грамм',  # углеводов 20 грамм
        r'(?:^|[,.\s])\s*у:?\s*(\d+(?:[.,]\d+)?)\s*г',  # у: 45г (с началом строки или разделителем)
        r'carbs?:?\s*(\d+(?:[.,]\d+)?)',
        r'(\d+(?:[.,]\d+)?)\s*g\s*carbs?',
        r'carbohydrates?:?\s*(\d+(?:[.,]\d+)?)',
        r'(\d+(?:[.,]\d+)?)\s*g\s*carbohydrates?',
        r'сахар[а-я]*:?\s*(\d+(?:[.,]\d+)?)'
    ]

    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            all_matches.extend([(float(m.replace(',', '.')), pattern) for m in matches])

    if all_matches:
        # Берем ПОСЛЕДНЕЕ найденное значение (обычно это итоговое)
        result, pattern = all_matches[-1]
        logging.info(f"📊 УГЛЕВОДЫ: Найдено {result}г по паттерну '{pattern}' (из {len(all_matches)} найденных)")
        return result

    logging.warning(f"📊 УГЛЕВОДЫ: НЕ НАЙДЕНО в тексте")
    return None


def extract_nutrition_smart(response_text: str) -> Dict[str, Optional[float]]:
    """Извлекает полные БЖУ и калории из ответа GPT"""
    logging.info(f"📊 ИЗВЛЕЧЕНИЕ БЖУ из ответа длиной {len(response_text)} символов")
    logging.info(f"📊 Первые 500 символов ответа: {response_text[:500]}")

    # КРИТИЧНО: Ищем секцию "ИТОГО" для извлечения финальных значений
    itogo_match = re.search(r'ИТОГО:?\s*(.+?)(?=\n\n|\Z)', response_text, re.IGNORECASE | re.DOTALL)
    
    if itogo_match:
        itogo_text = itogo_match.group(1)
        logging.info(f"📊 Найдена секция ИТОГО: {itogo_text[:200]}")
        
        # Пытаемся извлечь полный формат из секции ИТОГО
        full_pattern = r'(\d+(?:[.,]\d+)?)\s*ккал.*?(\d+(?:[.,]\d+)?)\s*г\s*белка.*?(\d+(?:[.,]\d+)?)\s*г\s*жиров?.*?(\d+(?:[.,]\d+)?)\s*г\s*углеводов?'
        full_match = re.search(full_pattern, itogo_text, re.IGNORECASE | re.DOTALL)
        
        if full_match:
            logging.info(f"📊 Найден полный формат БЖУ в ИТОГО: {full_match.groups()}")
            result = {
                'calories': int(float(full_match.group(1).replace(',', '.'))),
                'protein': float(full_match.group(2).replace(',', '.')),
                'fat': float(full_match.group(3).replace(',', '.')),
                'carbs': float(full_match.group(4).replace(',', '.'))
            }
            logging.info(f"📊 Результат из ИТОГО: {result}")
            return result
        else:
            # Извлекаем из секции ИТОГО по отдельности
            logging.info(f"📊 Извлекаем из ИТОГО по отдельности")
            calories = extract_calories_smart(itogo_text)
            protein = extract_protein_smart(itogo_text)
            fat = extract_fat_smart(itogo_text)
            carbs = extract_carbs_smart(itogo_text)
            
            if calories:  # Если хоть калории нашли в ИТОГО
                logging.info(f"📊 Извлечено из ИТОГО: калории={calories}, белки={protein}, жиры={fat}, углеводы={carbs}")
                result = {
                    'calories': calories,
                    'protein': protein,
                    'fat': fat,
                    'carbs': carbs
                }
                logging.info(f"📊 Финальный результат из ИТОГО: {result}")
                return result

    # Если секции ИТОГО нет, ищем полный формат по всему тексту
    logging.info(f"📊 Секция ИТОГО не найдена, ищем полный формат по всему тексту")
    full_pattern = r'(\d+(?:[.,]\d+)?)\s*ккал.*?(\d+(?:[.,]\d+)?)\s*г\s*белка.*?(\d+(?:[.,]\d+)?)\s*г\s*жиров?.*?(\d+(?:[.,]\d+)?)\s*г\s*углеводов?'
    
    # Ищем ВСЕ вхождения полного формата
    all_matches = list(re.finditer(full_pattern, response_text, re.IGNORECASE | re.DOTALL))
    
    if all_matches:
        # Берем ПОСЛЕДНЕЕ вхождение (обычно это итоговое значение)
        last_match = all_matches[-1]
        logging.info(f"📊 Найдено {len(all_matches)} полных форматов, берем последний: {last_match.groups()}")
        result = {
            'calories': int(float(last_match.group(1).replace(',', '.'))),
            'protein': float(last_match.group(2).replace(',', '.')),
            'fat': float(last_match.group(3).replace(',', '.')),
            'carbs': float(last_match.group(4).replace(',', '.'))
        }
        logging.info(f"📊 Результат последнего полного формата: {result}")
        return result

    # Если полный формат не найден, извлекаем по отдельности
    logging.info(f"📊 Полный формат не найден, извлекаем по частям")
    calories = extract_calories_smart(response_text)
    protein = extract_protein_smart(response_text)
    fat = extract_fat_smart(response_text)
    carbs = extract_carbs_smart(response_text)

    logging.info(f"📊 Извлечение по отдельности: калории={calories}, белки={protein}, жиры={fat}, углеводы={carbs}")

    result = {
        'calories': calories,
        'protein': protein,
        'fat': fat,
        'carbs': carbs
    }
    logging.info(f"📊 Финальный результат извлечения: {result}")
    return result


async def ask_gpt(messages: list, max_retries: int = 3) -> str:
    """
    Отправляет запрос к OpenAI GPT с автоматическими повторными попытками при таймауте
    
    Args:
        messages: Список сообщений для GPT
        max_retries: Максимальное количество повторных попыток (по умолчанию 3)
    
    Returns:
        str: Ответ от GPT
    
    Raises:
        Exception: Если все попытки исчерпаны или произошла критическая ошибка
    """
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI library not available")

    if 'client' not in globals() or client is None:
        raise Exception("OpenAI client not initialized")

    # Определяем модель: используем gpt-4o для vision задач, gpt-4o-mini для текста
    has_image = any(
        isinstance(msg.get('content'), list) and
        any(item.get('type') == 'image_url' for item in msg.get('content', []))
        for msg in messages
    )
    model = "gpt-4o" if has_image else "gpt-4o-mini"

    # Повторные попытки с экспоненциальной задержкой
    import asyncio
    for attempt in range(max_retries):
        try:
            logging.info(f"🔄 Попытка {attempt + 1}/{max_retries} отправки запроса к GPT ({model})")
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.1,
                timeout=60.0  # Устанавливаем таймаут 60 секунд
            )
            
            logging.info(f"✅ Успешный ответ от GPT на попытке {attempt + 1}")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Проверяем, является ли это ошибкой таймаута
            is_timeout = ('timeout' in error_msg.lower() or 
                         'timed out' in error_msg.lower() or
                         error_type in ['Timeout', 'TimedOut', 'TimeoutError'])
            
            # Проверяем, является ли это ошибкой перегрузки сервера
            is_overloaded = ('overloaded' in error_msg.lower() or
                           'rate limit' in error_msg.lower() or
                           error_type == 'RateLimitError')
            
            if attempt < max_retries - 1 and (is_timeout or is_overloaded):
                # Экспоненциальная задержка: 2, 4, 8 секунд
                wait_time = 2 ** (attempt + 1)
                logging.warning(
                    f"⚠️ {error_type}: {error_msg}. "
                    f"Повторная попытка через {wait_time} сек... "
                    f"(попытка {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
            else:
                # Последняя попытка или критическая ошибка
                logging.error(f"❌ OpenAI API error после {attempt + 1} попыток: {error_type} - {error_msg}")
                raise
    
    # Если все попытки исчерпаны
    raise Exception(f"Не удалось получить ответ от GPT после {max_retries} попыток")


def get_calories_left_message(profile: Dict[str, Any], diary: Dict[str, int],
                             burned: Dict[str, int], today: str) -> str:
    """
    Универсальная функция для расчёта оставшихся калорий
    """
    target_calories = profile.get('target_calories')
    old_target_limit = profile.get('target_limit')  # Совместимость со старыми профилями
    goal = profile.get('goal', 'deficit')
    is_custom_limit = profile.get('custom_limit', False)

    eaten_today = diary.get(today, 0)
    burned_today = burned.get(today, 0)

    if target_calories:
        # Система с лимитом калорий
        left = target_calories - eaten_today

        if is_custom_limit:
            # Пользовательский лимит
            if left > 0:
                left_message = f"Осталось до вашего лимита: {left} ккал"
                if burned_today > 0:
                    left_message += f" (+ {burned_today} ккал за активность)"
            else:
                left_message = f"Превышение вашего лимита: {abs(left)} ккал"
        else:
            # Автоматический расчет по цели
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


def calculate_macro_targets(weight: float, goal: str = 'deficit') -> Dict[str, float]:
    """
    Рассчитывает целевые значения БЖУ на основе веса и цели

    Рекомендации:
    - Белок: 1.6-2.2г на кг веса (в зависимости от цели)
    - Жиры: 0.8-1.2г на кг веса
    - Углеводы: остальные калории
    """

    if goal == 'deficit':
        # При похудении больше белка для сохранения мышц
        protein_per_kg = 2.0
        fat_per_kg = 0.8
    elif goal == 'surplus':
        # При наборе массы чуть меньше белка, больше углеводов
        protein_per_kg = 1.8
        fat_per_kg = 1.0
    else:  # maintain
        # При поддержании умеренные значения
        protein_per_kg = 1.8
        fat_per_kg = 0.9

    target_protein = weight * protein_per_kg
    target_fat = weight * fat_per_kg

    return {
        'protein': target_protein,
        'fat': target_fat,
        'protein_per_kg': protein_per_kg,
        'fat_per_kg': fat_per_kg
    }


def analyze_daily_nutrition(user_id: str, date: str = None) -> Dict[str, Any]:
    """
    Анализирует питание пользователя за день и возвращает статистику БЖУ
    """
    if not date:
        date = datetime.date.today().isoformat()

    food_log = get_user_food_log(user_id)
    daily_foods = food_log.get(date, [])

    if not daily_foods:
        return {
            'total_calories': 0,
            'total_protein': 0,
            'total_fat': 0,
            'total_carbs': 0,
            'foods_count': 0,
            'has_data': False
        }

    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0

    for food_entry in daily_foods:
        if len(food_entry) >= 2:
            calories = food_entry[1]
            total_calories += calories

            # Если есть информация о белке
            if len(food_entry) >= 3 and food_entry[2] is not None:
                protein = food_entry[2]
                total_protein += protein

            # Если есть информация о жирах
            if len(food_entry) >= 4 and food_entry[3] is not None:
                fat = food_entry[3]
                total_fat += fat

            # Если есть информация об углеводах
            if len(food_entry) >= 5 and food_entry[4] is not None:
                carbs = food_entry[4]
                total_carbs += carbs

    return {
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_carbs': total_carbs,
        'foods_count': len(daily_foods),
        'has_data': True
    }


def get_nutrition_recommendations(user_id: str, date: str = None) -> str:
    """
    Анализирует съеденное за день и дает рекомендации по питанию
    """
    if not date:
        date = datetime.date.today().isoformat()

    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    if not profile or 'weight' not in profile:
        return "❌ Для получения рекомендаций сначала заполните профиль командой /start"

    weight = profile['weight']
    goal = profile.get('goal', 'deficit')
    target_calories = profile.get('target_calories', 2000)

    # Получаем целевые значения БЖУ
    macro_targets = calculate_macro_targets(weight, goal)

    # Анализируем съеденное
    nutrition = analyze_daily_nutrition(user_id, date)

    if not nutrition['has_data']:
        return "📝 Сегодня еще нет записей о еде. Добавьте что-нибудь в дневник!"

    # Формируем рекомендации
    recommendations = []
    recommendations.append("🧠 **Анализ питания на сегодня:**\n")

    # Статистика по белкам
    protein_deficit = macro_targets['protein'] - nutrition['total_protein']
    protein_percent = (nutrition['total_protein'] / macro_targets['protein']) * 100 if macro_targets['protein'] > 0 else 0

    recommendations.append(f"🥩 **Белок:** {nutrition['total_protein']:.1f}г / {macro_targets['protein']:.1f}г ({protein_percent:.0f}%)")

    if protein_deficit > 20:
        recommendations.append(f"⚠️ Недостаток белка: {protein_deficit:.1f}г")
        recommendations.append("💡 *Рекомендации:* курица, творог, рыба, яйца, протеиновые коктейли")
    elif protein_deficit > 0:
        recommendations.append(f"📈 Можно добавить еще: {protein_deficit:.1f}г белка")
    else:
        recommendations.append("✅ Норма белка выполнена!")

    # Анализ по времени дня
    current_hour = datetime.datetime.now().hour

    if current_hour < 12:  # Утро
        recommendations.append(f"\n🌅 **Утренние рекомендации:**")
        if protein_deficit > 10:
            recommendations.append("• Добавьте белковый завтрак (яйца, творог, овсянка с протеином)")
        recommendations.append("• Не забудьте про сложные углеводы для энергии на день")

    elif current_hour < 18:  # День
        recommendations.append(f"\n☀️ **Дневные рекомендации:**")
        if protein_deficit > 15:
            recommendations.append("• Обед с хорошей порцией белка (мясо, рыба, бобовые)")
        recommendations.append("• Время для основного приема пищи")

    else:  # Вечер
        recommendations.append(f"\n🌙 **Вечерние рекомендации:**")
        if protein_deficit > 20:
            recommendations.append("• Легкий белковый ужин (рыба, творог, курица)")
            recommendations.append("• Избегайте тяжелых углеводов перед сном")
        elif protein_deficit > 0:
            recommendations.append("• Можно добавить легкий белковый перекус")
        else:
            recommendations.append("• Норма белка выполнена! Легкий ужин с овощами")

    # Общие рекомендации по балансу
    recommendations.append(f"\n⚖️ **Баланс питания:**")

    # Анализируем разнообразие (примерно)
    if nutrition['foods_count'] < 3:
        recommendations.append("📊 Мало разнообразия в питании - добавьте овощи и фрукты")

    # Рекомендации по калориям
    calories_left = target_calories - nutrition['total_calories']
    if calories_left > 300:
        recommendations.append(f"🔥 Осталось {calories_left} ккал - можно добавить полноценный прием пищи")
    elif calories_left > 100:
        recommendations.append(f"🔥 Осталось {calories_left} ккал - легкий перекус")
    elif calories_left > 0:
        recommendations.append(f"🔥 Осталось {calories_left} ккал - почти достигли цели")
    else:
        recommendations.append("🎯 Дневная норма калорий выполнена!")

    return '\n'.join(recommendations)


def get_food_suggestions_by_macros(protein_needed: float, calories_budget: int) -> list:
    """
    Предлагает конкретные продукты на основе недостающих макронутриентов
    """
    suggestions = []

    if protein_needed > 30:
        suggestions.extend([
            "🍗 Куриная грудка (150г) = 31г белка, 165 ккал",
            "🐟 Лосось (150г) = 37г белка, 231 ккал",
            "🥩 Говядина постная (100г) = 26г белка, 158 ккал"
        ])
    elif protein_needed > 15:
        suggestions.extend([
            "🥚 2 яйца = 12г белка, 140 ккал",
            "🧀 Творог 5% (100г) = 17г белка, 121 ккал",
            "🥛 Греческий йогурт (150г) = 15г белка, 100 ккал"
        ])
    elif protein_needed > 5:
        suggestions.extend([
            "🥜 Горсть миндаля = 6г белка, 160 ккал",
            "🍫 Протеиновый батончик = 8-12г белка, 120-180 ккал"
        ])

    # Ограничиваем по калориям
    filtered_suggestions = []
    for suggestion in suggestions:
        # Извлекаем калории из строки (примерно)
        try:
            calories_in_suggestion = int(suggestion.split('ккал')[0].split()[-1])
            if calories_in_suggestion <= calories_budget:
                filtered_suggestions.append(suggestion)
        except:
            filtered_suggestions.append(suggestion)  # Если не смогли распарсить, добавляем

    return filtered_suggestions[:3]  # Возвращаем максимум 3 предложения


def get_macro_analysis_command(user_id: str) -> str:
    """
    Полный анализ макронутриентов для команды /macros
    """
    today = datetime.date.today().isoformat()

    # Базовый анализ
    recommendations = get_nutrition_recommendations(user_id, today)

    # Получаем профиль для дополнительной информации
    profile = get_user_profile(user_id)
    nutrition = analyze_daily_nutrition(user_id, today)

    if profile and 'weight' in profile and nutrition['has_data']:
        weight = profile['weight']
        goal = profile.get('goal', 'deficit')
        target_calories = profile.get('target_calories', 2000)

        macro_targets = calculate_macro_targets(weight, goal)
        protein_needed = max(0, macro_targets['protein'] - nutrition['total_protein'])
        calories_left = max(0, target_calories - nutrition['total_calories'])

        if protein_needed > 5 and calories_left > 50:
            suggestions = get_food_suggestions_by_macros(protein_needed, calories_left)
            if suggestions:
                recommendations += f"\n\n💡 **Рекомендуемые продукты:**\n" + '\n'.join(f"• {s}" for s in suggestions)

    return recommendations
