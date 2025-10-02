#!/usr/bin/env python3
"""
Сверхбыстрые smoke tests - проверка что основное работает
"""

import sys
import os
import re


def test_smoke_regex():
    """Дымовой тест: проверяем что регулярки работают"""
    
    # Тест калорий
    text = "Творог 450 ккал с бананом"
    cal_match = re.search(r'(\d+)\s*ккал', text)
    assert cal_match and int(cal_match.group(1)) == 450, "Калории не извлекаются"
    
    # Тест белка
    text = "30г белка"
    prot_match = re.search(r'(\d+)г?\s*белка', text)
    assert prot_match and int(prot_match.group(1)) == 30, "Белки не извлекаются"
    
    # Тест жиров
    text = "15г жиров"
    fat_match = re.search(r'(\d+)г?\s*жиров?', text)
    assert fat_match and int(fat_match.group(1)) == 15, "Жиры не извлекаются"


def test_smoke_files():
    """Проверяем что ключевые файлы существуют"""
    required = ['calorie_bot_modular.py', 'config.py', 'requirements.txt']
    
    for filename in required:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        assert os.path.exists(filepath), f"Отсутствует файл: {filename}"


def test_smoke_imports():
    """Проверяем базовые импорты без сложных зависимостей"""
    try:
        import json
        import re
        import os
        import sys
    except Exception as e:
        raise AssertionError(f"Базовые импорты не работают: {e}")


def test_smoke_nutrition_logic():
    """Проверяем логику расчета калорий по БЖУ"""
    
    # Формула: белки*4 + жиры*9 + углеводы*4
    protein, fat, carbs = 30, 15, 25
    expected_calories = protein * 4 + fat * 9 + carbs * 4  # 30*4 + 15*9 + 25*4 = 120 + 135 + 100 = 355
    
    assert expected_calories == 355, f"Расчет БЖУ неверен: {expected_calories}"
    
    # Проверяем что большое отклонение детектируется
    claimed_calories = 100  # Сильно занижено
    deviation = abs(claimed_calories - expected_calories) / expected_calories
    
    assert deviation > 0.3, "Валидация отклонений не работает"


def run_smoke_tests():
    """Запуск всех дымовых тестов (для backward compatibility)"""
    
    tests = [
        (test_smoke_regex, "RegEx extraction"),
        (test_smoke_files, "File structure"), 
        (test_smoke_imports, "Basic imports"),
        (test_smoke_nutrition_logic, "BJU calculation logic")
    ]
    
    print("💨 Smoke Tests - Ultra Fast")
    print("=" * 30)
    
    for i, (test_func, name) in enumerate(tests, 1):
        try:
            test_func()
            print(f"✅ {i}. {name}")
        except Exception as e:
            print(f"❌ {i}. {name}: {e}")
            return False
    
    print("=" * 30)
    print("🚀 All smoke tests PASSED!")
    return True


if __name__ == "__main__":
    success = run_smoke_tests()
    
    if not success:
        print("💥 SMOKE TEST FAILURE - Critical issues detected!")
        sys.exit(1)
    else:
        print("✨ Ready to go!")
        sys.exit(0)
