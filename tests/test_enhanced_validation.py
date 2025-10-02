#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест усиленной валидации калорий для многокомпонентных блюд
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.nutrition_validator import validate_nutrition_data

def test_enhanced_validation():
    """Тестируем усиленную валидацию для сложных блюд"""
    
    print("🧪 ТЕСТ УСИЛЕННОЙ ВАЛИДАЦИИ КАЛОРИЙ")
    print("=" * 60)
    
    # Тест 1: Блюдо с курицей, булгуром, яйцом и овощами - заниженные калории
    description1 = "блюдо с курицей и гарниром: куриная грудка, отварной булгур, вареное яйцо, маринованные огурцы, красный перец"
    nutrition1 = {
        'calories': 380,  # Заниженное значение
        'protein': 31.0,
        'fat': 3.6,
        'carbs': 20.0
    }
    
    result1 = validate_nutrition_data(nutrition1, description1)
    print(f"Тест 1 - Исходные калории: {nutrition1['calories']} ккал")
    print(f"Тест 1 - После валидации: {result1['calories']} ккал")
    print(f"Тест 1 - Ожидаемо: 420+ ккал для 5 ингредиентов включая курицу+гарнир+яйцо")
    
    # Тест 2: Простое блюдо с курицей и рисом
    description2 = "куриная грудка с рисом"
    nutrition2 = {
        'calories': 350,
        'protein': 35.0,
        'fat': 4.0,
        'carbs': 25.0
    }
    
    result2 = validate_nutrition_data(nutrition2, description2)
    print(f"\nТест 2 - Исходные калории: {nutrition2['calories']} ккал")
    print(f"Тест 2 - После валидации: {result2['calories']} ккал")
    print(f"Тест 2 - Ожидаемо: 380+ ккал для курицы с гарниром")
    
    # Тест 3: Очень сложное блюдо с занижением
    description3 = "домашний обед: куриная грудка, рис, яйцо, огурцы, помидоры, зелень"
    nutrition3 = {
        'calories': 320,  # Сильно занижено для 6 ингредиентов
        'protein': 28.0,
        'fat': 2.0,
        'carbs': 15.0
    }
    
    result3 = validate_nutrition_data(nutrition3, description3)
    print(f"\nТест 3 - Исходные калории: {nutrition3['calories']} ккал")
    print(f"Тест 3 - После валидации: {result3['calories']} ккал")
    print(f"Тест 3 - Ожидаемо: 420+ ккал для 6 ингредиентов")
    
    print("\n" + "=" * 60)
    print("🎯 ПРОВЕРКА: Все сложные блюда должны иметь реалистичные калории (400+ ккал)")

if __name__ == "__main__":
    test_enhanced_validation()
