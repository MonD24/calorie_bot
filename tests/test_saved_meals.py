# -*- coding: utf-8 -*-
"""
Тесты для функциональности сохраненных блюд
"""
import pytest
import os
import json
import tempfile
import shutil

# Настраиваем путь до импортов
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Мокаем DATA_DIR до импорта user_data
import config


class TestSavedMeals:
    """Тесты для сохраненных блюд"""
    
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self, tmp_path, monkeypatch):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tmp_path / "test_data"
        self.temp_dir.mkdir()
        monkeypatch.setattr(config, 'DATA_DIR', str(self.temp_dir))
        
        # Импортируем после мока
        from utils.user_data import (
            get_user_saved_meals, save_user_saved_meals, 
            add_saved_meal, remove_saved_meal, get_user_files
        )
        self.get_user_saved_meals = get_user_saved_meals
        self.save_user_saved_meals = save_user_saved_meals
        self.add_saved_meal = add_saved_meal
        self.remove_saved_meal = remove_saved_meal
        self.get_user_files = get_user_files
    
    def test_get_empty_saved_meals(self):
        """Тест получения пустого списка блюд"""
        meals = self.get_user_saved_meals("test_user_1")
        assert meals == {}
    
    def test_add_saved_meal(self):
        """Тест добавления блюда"""
        user_id = "test_user_2"
        meal_name = "Творог с арбузом"
        meal_data = {
            'calories': 300,
            'protein': 25.0,
            'fat': 8.0,
            'carbs': 30.0
        }
        
        result = self.add_saved_meal(user_id, meal_name, meal_data)
        assert result is True
        
        # Проверяем что блюдо сохранилось
        saved_meals = self.get_user_saved_meals(user_id)
        assert len(saved_meals) == 1
        
        meal_key = meal_name.lower().strip()
        assert meal_key in saved_meals
        assert saved_meals[meal_key]['name'] == meal_name
        assert saved_meals[meal_key]['calories'] == 300
        assert saved_meals[meal_key]['protein'] == 25.0
    
    def test_add_multiple_meals(self):
        """Тест добавления нескольких блюд"""
        user_id = "test_user_3"
        
        meals_to_add = [
            ("Фрукты на вечер", {'calories': 150, 'protein': 1.0, 'fat': 0.5, 'carbs': 35.0}),
            ("Творог с пастой", {'calories': 450, 'protein': 30.0, 'fat': 20.0, 'carbs': 25.0}),
            ("Овсянка на молоке", {'calories': 250, 'protein': 10.0, 'fat': 5.0, 'carbs': 40.0}),
        ]
        
        for meal_name, meal_data in meals_to_add:
            self.add_saved_meal(user_id, meal_name, meal_data)
        
        saved_meals = self.get_user_saved_meals(user_id)
        assert len(saved_meals) == 3
    
    def test_remove_saved_meal(self):
        """Тест удаления блюда"""
        user_id = "test_user_4"
        meal_name = "Тестовое блюдо"
        
        self.add_saved_meal(user_id, meal_name, {'calories': 100})
        
        # Проверяем что блюдо добавилось
        saved_meals = self.get_user_saved_meals(user_id)
        assert len(saved_meals) == 1
        
        # Удаляем блюдо
        meal_key = meal_name.lower().strip()
        result = self.remove_saved_meal(user_id, meal_key)
        assert result is True
        
        # Проверяем что блюдо удалилось
        saved_meals = self.get_user_saved_meals(user_id)
        assert len(saved_meals) == 0
    
    def test_remove_nonexistent_meal(self):
        """Тест удаления несуществующего блюда"""
        user_id = "test_user_5"
        result = self.remove_saved_meal(user_id, "nonexistent_meal")
        assert result is False
    
    def test_meal_data_validation(self):
        """Тест сохранения блюда с частичными данными"""
        user_id = "test_user_6"
        meal_name = "Блюдо без БЖУ"
        
        # Сохраняем блюдо только с калориями
        self.add_saved_meal(user_id, meal_name, {'calories': 200})
        
        saved_meals = self.get_user_saved_meals(user_id)
        meal_key = meal_name.lower().strip()
        
        assert saved_meals[meal_key]['calories'] == 200
        assert saved_meals[meal_key]['protein'] is None
        assert saved_meals[meal_key]['fat'] is None
        assert saved_meals[meal_key]['carbs'] is None


class TestSaladCalorieValidation:
    """Тесты для валидации калорийности салатов"""
    
    def test_greek_salad_validation(self):
        """Тест что греческий салат не получает слишком низкую калорийность"""
        from utils.nutrition_validator import validate_nutrition_data
        
        # Симулируем ситуацию когда GPT занизил калории
        nutrition = {
            'calories': 150,  # Слишком мало для греческого салата
            'protein': 7.0,
            'fat': 10.0,  # Слишком мало жиров
            'carbs': 12.0
        }
        
        result = validate_nutrition_data(nutrition, "греческий салат с сыром фета и майонезом")
        
        # Калории должны быть увеличены
        assert result['calories'] >= 350
        # Жиры тоже должны быть увеличены
        assert result['fat'] >= 15
    
    def test_salad_with_dressing_validation(self):
        """Тест валидации салата с заправкой"""
        from utils.nutrition_validator import validate_nutrition_data
        
        nutrition = {
            'calories': 100,  # Слишком мало
            'protein': 2.0,
            'fat': 5.0,  # Слишком мало для салата с майонезом
            'carbs': 8.0
        }
        
        result = validate_nutrition_data(nutrition, "овощной салат с майонезом")
        
        # Калории должны быть увеличены
        assert result['calories'] >= 280
        # Жиры должны быть увеличены для салата с майонезом
        assert result['fat'] >= 18


class TestMultipleDishesValidation:
    """Тесты для валидации нескольких блюд на фото"""
    
    def test_two_dishes_low_calories(self):
        """Тест что два блюда не могут иметь слишком мало калорий"""
        from utils.nutrition_validator import validate_nutrition_data
        
        # Симулируем ситуацию когда GPT занизил калории для двух блюд
        nutrition = {
            'calories': 186,  # Критически мало для двух блюд
            'protein': 3.2,
            'fat': 10.7,
            'carbs': 19.4
        }
        
        result = validate_nutrition_data(nutrition, "два блюда: макароны с котлетами, морковь по-корейски с рыбой")
        
        # Калории должны быть значительно увеличены (минимум 700 для двух блюд)
        assert result['calories'] >= 700
    
    def test_pasta_with_cutlets_validation(self):
        """Тест валидации макарон с котлетами"""
        from utils.nutrition_validator import validate_nutrition_data
        
        nutrition = {
            'calories': 200,  # Слишком мало для макарон с котлетами
            'protein': 10.0,
            'fat': 8.0,
            'carbs': 25.0
        }
        
        result = validate_nutrition_data(nutrition, "макароны с котлетами")
        
        # Минимум 500 ккал для макарон с котлетами
        assert result['calories'] >= 500
    
    def test_korean_carrot_with_fish(self):
        """Тест валидации моркови по-корейски с рыбой"""
        from utils.nutrition_validator import validate_nutrition_data
        
        nutrition = {
            'calories': 100,  # Слишком мало
            'protein': 5.0,
            'fat': 5.0,
            'carbs': 10.0
        }
        
        result = validate_nutrition_data(nutrition, "морковь по-корейски с рыбой")
        
        # Должны быть увеличены калории и жиры
        assert result['calories'] >= 300  # Морковь по-корейски + рыба


class TestBJUExtraction:
    """Тесты для извлечения БЖУ из ответа GPT"""
    
    def test_extract_nutrition_from_itogo_no_spaces(self):
        """Тест извлечения БЖУ из формата ИТОГО без пробелов перед г"""
        from utils.calorie_calculator import extract_nutrition_smart
        
        # Реальный формат ответа GPT - без пробела перед "г"
        response = '''На фото:
1. Греческий салат ~350г - 806 ккал, 12г белка, 72г жира, 30г углеводов
2. Бокал пива ~500мл - 210 ккал, 1.5г белка, 0г жира, 17г углеводов

ИТОГО: 1016 ккал, 13.5г белка, 72г жира, 47г углеводов'''
        
        result = extract_nutrition_smart(response)
        
        assert result['calories'] == 1016
        assert result['protein'] == 13.5
        assert result['fat'] == 72
        assert result['carbs'] == 47
    
    def test_extract_nutrition_from_itogo_with_spaces(self):
        """Тест извлечения БЖУ из формата ИТОГО с пробелами перед г"""
        from utils.calorie_calculator import extract_nutrition_smart
        
        # Формат с пробелами
        response = '''На фото:
1. Творог с ягодами - 350 ккал, 25 г белка, 8 г жиров, 30 г углеводов

ИТОГО: 350 ккал, 25 г белка, 8 г жиров, 30 г углеводов'''
        
        result = extract_nutrition_smart(response)
        
        assert result['calories'] == 350
        assert result['protein'] == 25
        assert result['fat'] == 8
        assert result['carbs'] == 30
    
    def test_extract_nutrition_decimal_values(self):
        """Тест извлечения дробных значений БЖУ"""
        from utils.calorie_calculator import extract_nutrition_smart
        
        response = 'ИТОГО: 456 ккал, 23.5г белка, 15.8г жира, 42.3г углеводов'
        
        result = extract_nutrition_smart(response)
        
        assert result['calories'] == 456
        assert result['protein'] == 23.5
        assert result['fat'] == 15.8
        assert result['carbs'] == 42.3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
