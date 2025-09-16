#!/usr/bin/env python3
"""
Простые тесты для CI/CD без сложных зависимостей
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_bju_extraction_simple():
    """Простой тест извлечения БЖУ"""
    from utils.calorie_calculator import extract_nutrition_smart
    
    test_cases = [
        ("Творог 450 ккал, 30г белка, 15г жира, 25г углеводов", 450, 30, 15, 25),
        ("Салат: 320 ккал, белки 28г, жиры 12г, углеводы 8г", 320, 28, 12, 8),
        ("Калории: 280, белок: 22г, жиры: 18г, углеводы: 6г", 280, 22, 18, 6),
    ]
    
    passed = 0
    for text, exp_cal, exp_prot, exp_fat, exp_carb in test_cases:
        nutrition = extract_nutrition_smart(text)
        
        if (nutrition['calories'] == exp_cal and 
            nutrition['protein'] == exp_prot and
            nutrition['fat'] == exp_fat and 
            nutrition['carbs'] == exp_carb):
            passed += 1
        else:
            print(f"❌ Не прошел: {text}")
            print(f"   Ожидалось: {exp_cal}, {exp_prot}, {exp_fat}, {exp_carb}")
            print(f"   Получено: {nutrition['calories']}, {nutrition['protein']}, {nutrition['fat']}, {nutrition['carbs']}")
    
    return passed == len(test_cases)


def test_nutrition_validation_simple():
    """Простой тест валидации"""
    from utils.nutrition_validator import validate_nutrition_data
    
    # Тест коррекции калорий
    nutrition = {"calories": 159, "protein": 32.5, "fat": 26.4, "carbs": 29.2}
    validated = validate_nutrition_data(nutrition, "Творог")
    
    # Калории должны быть исправлены на основе БЖУ
    return validated['calories'] > 400


def test_imports():
    """Тест что все модули корректно импортируются"""
    try:
        from utils.calorie_calculator import extract_nutrition_smart
        from utils.nutrition_validator import validate_nutrition_data
        from utils.photo_processor import analyze_food_photo
        from handlers.commands import help_command
        from data.calorie_database import CALORIE_DATABASE
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False


def test_mock_responses():
    """Тест мок-ответов"""
    try:
        from tests.mock_gpt import MockGPTResponses, mock_ask_gpt
        
        # Проверяем что моки возвращают данные
        response = MockGPTResponses.PHOTO_RESPONSES["творог_банан"]
        if "450 ккал" not in response:
            return False
        
        # Проверяем мок функцию
        result = mock_ask_gpt([{"content": "гречка с котлетой"}])
        if "480 ккал" not in result:
            return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка моков: {e}")
        return False


def main():
    """Запуск всех простых тестов"""
    tests = [
        (test_imports, "Импорт модулей"),
        (test_bju_extraction_simple, "Извлечение БЖУ"),
        (test_nutrition_validation_simple, "Валидация питания"),
        (test_mock_responses, "Мок-ответы GPT"),
    ]
    
    print("🧪 Запуск простых тестов для CI/CD:\n")
    
    passed = 0
    total = len(tests)
    
    for test_func, test_name in tests:
        try:
            if test_func():
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}: тест вернул False")
        except Exception as e:
            print(f"❌ {test_name}: {e}")
    
    print(f"\n📊 Результаты: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты успешны!")
        return True
    else:
        print("🔧 Есть проблемы, нужны исправления")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
