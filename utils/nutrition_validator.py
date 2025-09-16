# -*- coding: utf-8 -*-
"""
Валидатор питательных данных
"""
import logging
from typing import Dict, Any, Optional


def validate_nutrition_data(nutrition: Dict[str, Any], description: str) -> Dict[str, Any]:
    """
    Проверяет логичность данных о питании и исправляет явные ошибки
    """
    validated = nutrition.copy()
    warnings = []
    
    calories = nutrition.get('calories')
    protein = nutrition.get('protein')
    fat = nutrition.get('fat') 
    carbs = nutrition.get('carbs')
    
    # Проверяем соотношение БЖУ и калорий
    if all(x is not None for x in [calories, protein, fat, carbs]):
        # Калории из БЖУ: белки и углеводы = 4 ккал/г, жиры = 9 ккал/г
        calculated_calories = protein * 4 + fat * 9 + carbs * 4
        
        # Допустимое отклонение 20%
        if abs(calories - calculated_calories) / calculated_calories > 0.3:
            warnings.append(f"Несоответствие калорий: заявлено {calories}, по БЖУ {calculated_calories:.0f}")
            
            # Если расхождение критическое, используем расчет по БЖУ
            if calories < calculated_calories * 0.6:
                validated['calories'] = int(calculated_calories)
                warnings.append(f"Калории исправлены на {int(calculated_calories)}")
    
    # Проверяем на типичные ошибки GPT
    if 'творог' in description.lower():
        # Творог: примерно 100-180 ккал/100г в зависимости от жирности
        if calories and calories < 80:  # Подозрительно мало для творога
            warnings.append("Подозрительно низкая калорийность для творога")
            
        if protein and protein > 40:  # В твороге макс ~18г белка/100г
            warnings.append("Подозрительно много белка для творога")
    
    if 'банан' in description.lower() and calories and calories < 50:
        warnings.append("Подозрительно низкая калорийность для блюда с бананом")
    
    # Проверяем базовые пределы
    if protein and protein < 0.5:
        validated['protein'] = 0.5
    if fat and fat < 0.1:
        validated['fat'] = 0.1
    if carbs and carbs < 0.5:
        validated['carbs'] = 0.5
        
    # Логируем предупреждения
    if warnings:
        logging.warning(f"Валидация питания для '{description}': {'; '.join(warnings)}")
    
    return validated


def estimate_portion_calories(description: str, ingredients: list = None) -> Optional[int]:
    """
    Оценивает примерную калорийность на основе описания
    """
    description_lower = description.lower()
    estimated_calories = 0
    
    # Базовые продукты и их типичная калорийность на порцию
    food_calories = {
        'творог': 150,  # ~100г порция
        'банан': 90,    # средний банан
        'яйцо': 70,     # 1 яйцо
        'курица': 200,  # ~100г
        'рис': 130,     # порция вареного
        'гречка': 120,  # порция вареной
        'хлеб': 80,     # кусок
        'масло': 100,   # ст. ложка
        'арахисовая паста': 120,  # ~2 ст.л.
    }
    
    for food, cal in food_calories.items():
        if food in description_lower:
            estimated_calories += cal
    
    # Корректировки по контексту
    if 'салат' in description_lower and estimated_calories < 200:
        estimated_calories += 100  # заправка, овощи
        
    return estimated_calories if estimated_calories > 50 else None
