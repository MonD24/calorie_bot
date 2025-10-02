# -*- coding: utf-8 -*-
"""
Тестовый скрипт с логированием для отладки валидации
"""
import sys
import logging
from pathlib import Path

# Настраиваем детальное логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('validation_debug.log', encoding='utf-8')
    ]
)

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from utils.calorie_calculator import extract_nutrition_smart
from utils.nutrition_validator import validate_nutrition_data, estimate_portion_calories


def test_gpt_response_processing():
    """Тестируем обработку ответа GPT с детальным логированием"""
    
    print("=== ТЕСТ ОБРАБОТКИ ОТВЕТА GPT С ЛОГИРОВАНИЕМ ===")
    
    # Имитируем реальный ответ GPT для блюда с фото
    test_responses = [
        # Тест 1: Ответ с нулевыми жирами и углеводами (как в реальной проблеме)
        """На фото блюдо с куриной грудкой - кусочки жареной курицы, рис, яйцо, маринованные огурцы.

Куриная грудка ~120г: 165×1.2 = 198 ккал, 37г белка, 4г жиров, 0г углеводов
ИТОГО: 198 ккал, 37г белка, 4г жиров, 0г углеводов""",
        
        # Тест 2: Полный правильный ответ
        """На фото куриная грудка с рисом - кусочки курицы, порция риса, яйцо, огурцы.

Куриная грудка ~120г: 165×1.2 = 198 ккал, 37г белка, 4г жиров, 0г углеводов
Рис отварной ~100г: 116×1.0 = 116 ккал, 2.2г белка, 0.5г жиров, 23г углеводов
Яйцо ~50г: 155×0.5 = 78 ккал, 6.5г белка, 5.5г жиров, 0.4г углеводов

ИТОГО: 392 ккал, 45.7г белка, 10г жиров, 23.4г углеводов"""
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n{'='*60}")
        print(f"ТЕСТ {i}")
        print('='*60)
        print(f"Ответ GPT:\n{response}")
        print('\n' + '-'*40)
        
        # Извлекаем питательные данные
        print("🔍 ИЗВЛЕЧЕНИЕ ДАННЫХ:")
        nutrition = extract_nutrition_smart(response)
        
        # Валидируем данные
        print("\n🔧 ВАЛИДАЦИЯ:")
        description = "блюдо с куриной грудкой"
        validated = validate_nutrition_data(nutrition, description)
        
        print(f"\n📊 РЕЗУЛЬТАТ:")
        print(f"Исходно: {nutrition}")
        print(f"После валидации: {validated}")
        
        print(f"\n🎯 ИТОГ:")
        print(f"Калории: {nutrition.get('calories')} -> {validated.get('calories')}")
        print(f"Белки: {nutrition.get('protein')} -> {validated.get('protein')}")
        print(f"Жиры: {nutrition.get('fat')} -> {validated.get('fat')}")
        print(f"Углеводы: {nutrition.get('carbs')} -> {validated.get('carbs')}")


if __name__ == "__main__":
    test_gpt_response_processing()
    print(f"\n📋 Детальные логи сохранены в файл: validation_debug.log")
