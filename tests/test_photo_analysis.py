#!/usr/bin/env python3
"""
Тесты для анализа фотографий еды (с моками GPT)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest
except ImportError:
    pytest = None

import asyncio
from unittest.mock import patch, MagicMock
from tests.mock_gpt import MockGPTContext, mock_gpt_analyze_photo, mock_ask_gpt


class TestPhotoAnalysis:
    """Тесты для анализа фотографий еды"""
    
    def test_photo_analysis_success(self):
        """Тест успешного анализа фотографии"""
        # Используем мок вместо реального GPT
        result = mock_gpt_analyze_photo("test_image_data")
        
        assert result['success'] is True
        assert result['calories'] == 450
        assert result['protein'] == 30.5
        assert result['fat'] == 23.8
        assert result['carbs'] == 30.0
        assert 'description' in result
    
    def test_photo_analysis_error(self):
        """Тест обработки ошибок при анализе"""
        result = mock_gpt_analyze_photo("error_image_data")
        
        assert 'error' in result
        assert result['error'] == "Не удалось проанализировать изображение"
    
    def test_photo_analysis_question(self):
        """Тест когда GPT задает уточняющий вопрос"""
        result = mock_gpt_analyze_photo("question_image_data")
        
        assert 'question' in result
        assert result['question'] == "Можете уточнить размер порции?"


class TestPhotoProcessorIntegration:
    """Интеграционные тесты для photo_processor"""
    
    def test_extract_nutrition_from_response(self):
        """Тест извлечения питательных данных из ответа GPT"""
        from utils.calorie_calculator import extract_nutrition_smart
        from tests.mock_gpt import MockGPTResponses
        
        # Тестируем с мок-ответом
        response = MockGPTResponses.PHOTO_RESPONSES["творог_банан"]
        nutrition = extract_nutrition_smart(response)
        
        assert nutrition['calories'] == 450
        assert nutrition['protein'] == 30.5
        assert nutrition['fat'] == 23.8
        assert nutrition['carbs'] == 30.0
    
    def test_extract_nutrition_with_validation(self):
        """Тест извлечения + валидации"""
        from utils.calorie_calculator import extract_nutrition_smart
        from utils.nutrition_validator import validate_nutrition_data
        from tests.mock_gpt import MockGPTResponses
        
        # Используем неправильный ответ
        response = MockGPTResponses.PHOTO_RESPONSES["неправильный_ответ"]
        nutrition = extract_nutrition_smart(response)
        
        # Проверяем что извлекли неправильные данные
        assert nutrition['calories'] == 159
        
        # Валидируем
        validated = validate_nutrition_data(nutrition, "Творог с бананом")
        
        # Калории должны быть исправлены
        assert validated['calories'] > 400
    
    def test_async_photo_analysis_mock(self):
        """Тест асинхронного анализа фото с моком"""
        async def run_test():
            with patch('utils.photo_processor.ask_gpt', side_effect=mock_ask_gpt):
                from utils.photo_processor import analyze_food_photo
                
                # Тестируем с фейковыми данными изображения
                result = await analyze_food_photo("fake_base64_image_data")
                
                # Проверяем что получили корректные данные
                assert 'description' in result
                assert 'calories' in result
                assert result['success'] is True
        
        # Запускаем асинхронный тест
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(run_test())


class TestBJUExtractionMocked:
    """Тесты извлечения БЖУ с мокированными ответами"""
    
    def test_various_format_extraction(self):
        """Тест извлечения различных форматов без реальных API вызовов"""
        from utils.calorie_calculator import extract_nutrition_smart
        from tests.mock_gpt import MockGPTResponses
        
        test_cases = [
            (MockGPTResponses.PHOTO_RESPONSES["творог_банан"], 450, 30.5),
            (MockGPTResponses.PHOTO_RESPONSES["омлет"], 325, 19.5),
            (MockGPTResponses.PHOTO_RESPONSES["салат_курица"], 317, 32.8),
            (MockGPTResponses.TEXT_RESPONSES["гречка котлета"], 480, 35.0),
        ]
        
        for response, expected_cal, expected_protein in test_cases:
            nutrition = extract_nutrition_smart(response)
            assert nutrition['calories'] == expected_cal
            assert nutrition['protein'] == expected_protein
    
    def test_mock_gpt_text_responses(self):
        """Тест мок-ответов для текстовых запросов"""
        # Тестируем мок функцию напрямую
        response = mock_ask_gpt([{"content": "Сколько калорий в гречке с котлетой?"}])
        assert "480 ккал" in response
        assert "35 г белка" in response
        
        response = mock_ask_gpt([{"content": "Анализ борща"}])
        assert "350 ккал" in response
        assert "25 г белка" in response


def run_photo_tests():
    """Запуск всех тестов фотоанализа без pytest"""
    test_photo = TestPhotoAnalysis()
    test_processor = TestPhotoProcessorIntegration()
    test_bju = TestBJUExtractionMocked()
    
    tests = [
        (test_photo.test_photo_analysis_success, "Успешный анализ фото"),
        (test_photo.test_photo_analysis_error, "Обработка ошибок"),
        (test_photo.test_photo_analysis_question, "Уточняющие вопросы"),
        (test_processor.test_extract_nutrition_from_response, "Извлечение из ответа"),
        (test_processor.test_extract_nutrition_with_validation, "Извлечение + валидация"),
        (test_processor.test_async_photo_analysis_mock, "Асинхронный анализ"),
        (test_bju.test_various_format_extraction, "Различные форматы"),
        (test_bju.test_mock_gpt_text_responses, "Мок-ответы GPT"),
    ]
    
    passed = 0
    failed = 0
    
    print("🧪 Запуск тестов анализа фотографий (с моками):\n")
    
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
        success = run_photo_tests()
        sys.exit(0 if success else 1)
