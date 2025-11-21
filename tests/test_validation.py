#!/usr/bin/env python3
"""
Pytest-совместимые тесты для валидации питания
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest
except ImportError:
    pytest = None

from utils.nutrition_validator import validate_nutrition_data, estimate_portion_calories
from tests.mock_gpt import MockGPTContext, with_mock_gpt


class TestNutritionValidation:
    """Тесты для валидации питательных данных"""
    
    def test_calorie_correction_from_bju(self):
        """Тест коррекции калорий на основе БЖУ"""
        # Неправильные калории, но правильные БЖУ
        nutrition = {"calories": 159, "protein": 32.5, "fat": 26.4, "carbs": 29.2}
        validated = validate_nutrition_data(nutrition, "Творог с бананом")
        
        # Калории должны быть пересчитаны: 32.5*4 + 26.4*9 + 29.2*4 ≈ 484
        assert validated['calories'] > 400
        assert validated['protein'] == 32.5  # Остальные значения не меняются
    
    def test_tuna_salad_calorie_correction(self):
        """Тест коррекции калорий для салата с тунцом (реальный кейс)"""
        # Реальные данные от GPT: калории занижены, БЖУ правильные
        nutrition = {"calories": 300, "protein": 31.9, "fat": 38.9, "carbs": 18.0}
        validated = validate_nutrition_data(nutrition, "салат с тунцом: консервированный тунец в масле, огурцы, сухарики, вареное яйцо, майонез")
        
        # По БЖУ: 31.9*4 + 38.9*9 + 18.0*4 = 550 ккал
        # Калории должны быть исправлены на основе БЖУ
        assert validated['calories'] >= 500, f"Expected >= 500 kcal, got {validated['calories']}"
        assert validated['calories'] <= 600, f"Expected <= 600 kcal, got {validated['calories']}"
        # БЖУ не должны измениться
        assert validated['protein'] == 31.9
        assert validated['fat'] == 38.9
        assert validated['carbs'] == 18.0
        
    def test_no_correction_for_valid_data(self):
        """Тест что корректные данные не изменяются"""
        nutrition = {"calories": 450, "protein": 31.5, "fat": 23.8, "carbs": 31.5}
        validated = validate_nutrition_data(nutrition, "Творог с бананом")
        
        assert validated == nutrition  # Данные не должны измениться
    
    def test_minimum_values_correction(self):
        """Тест коррекции минимальных значений"""
        nutrition = {"calories": 100, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        validated = validate_nutrition_data(nutrition, "Тест")
        
        # Проверяем что значения больше нуля (точные значения могут отличаться)
        assert validated['protein'] > 0     # Минимум для белка
        assert validated['fat'] > 0         # Минимум для жира  
        assert validated['carbs'] > 0       # Минимум для углеводов
    
    def test_portion_estimation(self):
        """Тест оценки калорийности порций"""
        # Творог с бананом должен давать примерную оценку
        estimated = estimate_portion_calories("творог с бананом")
        assert estimated is not None
        assert estimated > 0  # Просто проверяем что есть оценка
        
        # Салат с курицей
        estimated = estimate_portion_calories("салат с курицей и овощами")
        assert estimated is not None
        assert estimated > 0
    
    def test_unknown_food_estimation(self):
        """Тест оценки неизвестной еды"""
        estimated = estimate_portion_calories("неизвестное блюдо xyz")
        assert estimated is None or estimated == 0


class TestIntegration:
    """Интеграционные тесты"""
    
    def test_full_pipeline(self):
        """Тест полного цикла: извлечение + валидация"""
        # Используем мок чтобы не вызывать реальный GPT
        with MockGPTContext():
            from utils.calorie_calculator import extract_nutrition_smart
            
            # Неправильный ответ GPT (тестируем извлечение напрямую)
            gpt_response = "Творог 159 ккал, 32.5г белка, 26.4г жира, 29.2г углеводов"
            
            # Извлекаем данные
            nutrition = extract_nutrition_smart(gpt_response)
            assert nutrition['calories'] == 159
            
            # Валидируем
            validated = validate_nutrition_data(nutrition, "Творог")
            assert validated['calories'] > 400  # Должно быть исправлено
    
    def test_import_integrity(self):
        """Тест целостности импортов"""
        # Проверяем что все модули импортируются без ошибок
        try:
            from utils.calorie_calculator import extract_nutrition_smart
            from utils.photo_processor import analyze_food_photo
            from handlers.commands import help_command
            from data.calorie_database import CALORIE_DATABASE
            assert True  # Если дошли сюда - импорты работают
        except ImportError as e:
            assert False, f"Import error: {e}"


def run_tests():
    """Запуск тестов без pytest"""
    test_validation = TestNutritionValidation()
    test_integration = TestIntegration()
    
    tests = [
        (test_validation.test_calorie_correction_from_bju, "Коррекция калорий"),
        (test_validation.test_tuna_salad_calorie_correction, "Салат с тунцом (реальный кейс)"),
        (test_validation.test_no_correction_for_valid_data, "Валидные данные"),
        (test_validation.test_minimum_values_correction, "Минимальные значения"),
        (test_validation.test_portion_estimation, "Оценка порций"),
        (test_validation.test_unknown_food_estimation, "Неизвестная еда"),
        (test_integration.test_full_pipeline, "Полный цикл"),
        (test_integration.test_import_integrity, "Целостность импортов"),
    ]
    
    passed = 0
    failed = 0
    
    print("🧪 Запуск тестов валидации:\n")
    
    for test_func, test_name in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    print(f"\n📊 Результаты: {passed} прошли, {failed} упали")
    return failed == 0


if __name__ == "__main__":
    if pytest:
        pytest.main([__file__, "-v"])
    else:
        success = run_tests()
        sys.exit(0 if success else 1)
