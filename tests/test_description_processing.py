# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки извлечения данных из описания
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from utils.calorie_calculator import extract_nutrition_smart
from utils.nutrition_validator import validate_nutrition_data, estimate_portion_calories


def test_description_processing():
    """Тестируем обработку описания блюда как с фото"""
    
    print("=== Тест обработки описания блюда с фото ===")
    
    # Имитируем ответ GPT для блюда с фото
    simulated_gpt_response = """На фото куриная грудка с рисом и овощами - кусочки жареной курицы, порция отварного риса, вареное яйцо, маринованные огурцы.

Куриная грудка жареная ~120г: 165×1.2 = 198 ккал, 31г белка, 4г жиров, 0г углеводов
Рис отварной ~100г: 116×1.0 = 116 ккал, 2.2г белка, 0.5г жиров, 23г углеводов
Яйцо вареное ~50г: 155×0.5 = 78 ккал, 6.5г белка, 5.5г жиров, 0.4г углеводов
Огурцы маринованные ~60г: 16×0.6 = 10 ккал, 0.5г белка, 0г жиров, 2г углеводов

ИТОГО: 402 ккал, 40.2 г белка, 10 г жиров, 25.4 г углеводов"""
    
    print("Имитация ответа GPT:")
    print(simulated_gpt_response)
    print("\n" + "="*50)
    
    # Извлекаем питательные данные
    nutrition = extract_nutrition_smart(simulated_gpt_response)
    print(f"\nИзвлеченные данные: {nutrition}")
    
    # Валидируем данные
    description = "куриная грудка с рисом и овощами"
    validated = validate_nutrition_data(nutrition, description)
    print(f"После валидации: {validated}")
    
    print(f"\n=== Сравнение с оригинальным результатом бота ===")
    print("Бот определил: 165 ккал, 31г белка, 3.6г жиров")
    print(f"Наша система: {validated['calories']} ккал, {validated['protein']}г белка, {validated['fat']}г жиров")
    print(f"Улучшение: +{validated['calories'] - 165} ккал")


def test_real_photo_description():
    """Тестируем с реальным описанием блюда с фото"""
    
    print(f"\n=== Тест с реальным описанием блюда ===")
    
    # Реальное описание блюда с фото
    real_descriptions = [
        "блюдо с куриной грудкой",  # То, что определил бот
        "куриная грудка с рисом и яйцом",  # Более точное описание
        "куриная грудка с булгуром, вареное яйцо, маринованные огурцы"  # Полное описание
    ]
    
    for desc in real_descriptions:
        print(f"\nОписание: '{desc}'")
        
        # Имитируем заниженные данные бота
        low_nutrition = {
            'calories': 165,
            'protein': 31.0,
            'fat': 3.6,
            'carbs': None
        }
        
        # Валидируем
        validated = validate_nutrition_data(low_nutrition, desc)
        estimated = estimate_portion_calories(desc)
        
        print(f"  Исходно: {low_nutrition['calories']} ккал")
        print(f"  После валидации: {validated['calories']} ккал")
        print(f"  Оценка по описанию: {estimated} ккал")


if __name__ == "__main__":
    test_description_processing()
    test_real_photo_description()
