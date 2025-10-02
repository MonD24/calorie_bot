# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки анализа фото
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from utils.photo_processor import analyze_food_photo
from utils.nutrition_validator import validate_nutrition_data, estimate_portion_calories


async def test_photo_analysis():
    """Тестируем улучшенный анализ фото"""
    
    # Тестируем валидацию без фото
    print("=== Тест валидации питательных данных ===")
    
    # Тест 1: Блюдо с курицей с заниженными калориями
    test_nutrition1 = {
        'calories': 165,
        'protein': 31.0,
        'fat': 3.6,
        'carbs': None
    }
    test_description1 = "блюдо с куриной грудкой"
    
    validated1 = validate_nutrition_data(test_nutrition1, test_description1)
    print(f"\nТест 1 - '{test_description1}':")
    print(f"Исходно: {test_nutrition1}")
    print(f"После валидации: {validated1}")
    
    # Тест 2: Сложное блюдо с несколькими ингредиентами
    test_nutrition2 = {
        'calories': 180,
        'protein': 25.0,
        'fat': 5.0,
        'carbs': 15.0
    }
    test_description2 = "куриная грудка с рисом и яйцом"
    
    validated2 = validate_nutrition_data(test_nutrition2, test_description2)
    print(f"\nТест 2 - '{test_description2}':")
    print(f"Исходно: {test_nutrition2}")
    print(f"После валидации: {validated2}")
    
    # Тест 3: Оценка калорий по описанию
    test_descriptions = [
        "блюдо с куриной грудкой",
        "куриная грудка с рисом",
        "курица с булгуром и яйцом", 
        "куриная грудка с рисом и огурцами",
        "курица, рис, яйцо, огурцы маринованные"
    ]
    
    print(f"\n=== Тест оценки калорий по описанию ===")
    for desc in test_descriptions:
        estimated = estimate_portion_calories(desc)
        print(f"'{desc}' -> {estimated} ккал")


if __name__ == "__main__":
    asyncio.run(test_photo_analysis())
