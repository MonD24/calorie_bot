# -*- coding: utf-8 -*-
"""
Простой тест для проверки валидации реального случая
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from utils.nutrition_validator import validate_nutrition_data


def test_real_case():
    """Тестируем реальный случай с фото"""
    
    print("=== ТЕСТ РЕАЛЬНОГО СЛУЧАЯ С ФОТО ===")
    
    # Реальные данные, которые определил бот (последний результат)
    real_nutrition = {
        'calories': 350,  # Уже исправлено
        'protein': 1.1,   # ❌ Новая проблема!
        'fat': 6.0,       # Уже исправлено
        'carbs': 18.0     # Уже исправлено
    }
    
    real_description = "блюдо с куриной грудкой"
    
    print(f"Описание: '{real_description}'")
    print(f"Исходные данные: {real_nutrition}")
    
    # Валидируем
    validated = validate_nutrition_data(real_nutrition, real_description)
    
    print(f"После валидации: {validated}")
    
    # Проверяем исправления
    changes = []
    for key in ['calories', 'protein', 'fat', 'carbs']:
        old_val = real_nutrition.get(key)
        new_val = validated.get(key)
        if old_val != new_val:
            changes.append(f"{key}: {old_val} -> {new_val}")
    
    if changes:
        print(f"\n✅ ИСПРАВЛЕНИЯ:")
        for change in changes:
            print(f"  • {change}")
    else:
        print(f"\n❌ НЕТ ИСПРАВЛЕНИЙ!")
        
    # Проверяем ожидаемые результаты
    expected_min = {
        'calories': 300,
        'protein': 25.0,  # Добавили проверку белка
        'fat': 4.0,
        'carbs': 15.0
    }
    
    print(f"\n📊 ПРОВЕРКА МИНИМУМОВ:")
    all_good = True
    for key, min_val in expected_min.items():
        actual = validated.get(key, 0)
        status = "✅" if actual >= min_val else "❌"
        print(f"  {status} {key}: {actual} (мин. {min_val})")
        if actual < min_val:
            all_good = False
    
    if all_good:
        print(f"\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    else:
        print(f"\n⚠️ ЕСТЬ ПРОБЛЕМЫ!")


if __name__ == "__main__":
    test_real_case()
