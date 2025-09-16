#!/usr/bin/env python3
"""
Pytest-совместимые тесты для извлечения БЖУ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.calorie_calculator import extract_nutrition_smart


class TestBJUExtraction:
    """Тесты для извлечения БЖУ из ответов GPT"""
    
    def test_full_format_extraction(self):
        """Тест извлечения полного формата БЖУ"""
        response = "Творог с бананом и арахисовой пастой. Итого: 450 ккал, 30 г белка, 15 г жиров, 25 г углеводов"
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 450.0
        assert nutrition['protein'] == 30.0
        assert nutrition['fat'] == 15.0
        assert nutrition['carbs'] == 25.0
    
    def test_alternative_format_extraction(self):
        """Тест извлечения альтернативного формата"""
        response = "Салат с курицей: 320 ккал, белки 28г, жиры 12г, углеводы 8г"
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 320
        assert nutrition['protein'] == 28.0
        assert nutrition['fat'] == 12.0
        assert nutrition['carbs'] == 8.0
    
    def test_multiline_format_extraction(self):
        """Тест извлечения многострочного формата"""
        response = """Омлет с сыром и помидорами.
Калорийность: 280 ккал
Белки: 22 г
Жиры: 18 г
Углеводы: 6 г"""
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 280
        assert nutrition['protein'] == 22.0
        assert nutrition['fat'] == 18.0
        assert nutrition['carbs'] == 6.0
    
    def test_gram_format_extraction(self):
        """Тест извлечения формата с 'грамм'"""
        response = "Борщ с мясом - 350 калорий, 25 грамм белка, жирность 10 грамм, углеводов 20 грамм"
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 350
        assert nutrition['protein'] == 25.0
        assert nutrition['fat'] == 10.0
        assert nutrition['carbs'] == 20.0
    
    def test_abbreviated_format_extraction(self):
        """Тест извлечения сокращенного формата Б/Ж/У"""
        response = "Гречка с котлетой. Всего 480 ккал, б: 35г, ж: 16г, у: 45г"
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 480
        assert nutrition['protein'] == 35.0
        assert nutrition['fat'] == 16.0
        assert nutrition['carbs'] == 45.0
    
    def test_bullet_format_extraction(self):
        """Тест извлечения формата со списком"""
        response = """Рис с курицей и овощами
• Калории: 420
• Белок: 32 г
• Ж: 8 г
• У: 55 г"""
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 420
        assert nutrition['protein'] == 32.0
        assert nutrition['fat'] == 8.0
        assert nutrition['carbs'] == 55.0
    
    def test_empty_response(self):
        """Тест обработки пустого ответа"""
        nutrition = extract_nutrition_smart("")
        
        assert nutrition['calories'] is None
        assert nutrition['protein'] is None
        assert nutrition['fat'] is None
        assert nutrition['carbs'] is None
    
    def test_partial_data(self):
        """Тест обработки частичных данных"""
        response = "Салат: 200 ккал, белки 15г"
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 200
        assert nutrition['protein'] == 15.0
        assert nutrition['fat'] is None
        assert nutrition['carbs'] is None
    
    @pytest.mark.parametrize("calories,protein,fat,carbs,expected_valid", [
        (450, 30.0, 15.0, 25.0, True),  # Правильные данные
        (0, 0, 0, 0, False),  # Нулевые значения
        (None, None, None, None, False),  # Пустые значения
        (200, 20.0, None, None, True),  # Частичные данные
    ])
    def test_data_validation(self, calories, protein, fat, carbs, expected_valid):
        """Параметризованный тест валидации данных"""
        nutrition = {
            'calories': calories,
            'protein': protein, 
            'fat': fat,
            'carbs': carbs
        }
        
        has_valid_data = any(v is not None and v > 0 for v in nutrition.values())
        assert has_valid_data == expected_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
