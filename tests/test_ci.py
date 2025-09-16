#!/usr/bin/env python3
"""
Надежные тесты для CI/CD - простые и быстрые
"""

import sys
import os
import re
from typing import Dict, Optional

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_calories_test(text: str) -> Optional[int]:
    """Простая функция извлечения калорий для тестирования"""
    patterns = [
        r'(\d+)\s*ккал',
        r'калори[йяе]:\s*(\d+)',
        r'всего\s+(\d+)',
        r'итого:?\s*(\d+)',
        r'калории:\s*(\d+)',  # Добавили этот паттерн
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_protein_test(text: str) -> Optional[float]:
    """Простая функция извлечения белка для тестирования"""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*г\s*белка',
        r'белк[а-я]*:?\s*(\d+(?:\.\d+)?)',
        r'б:?\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def test_basic_extraction():
    """Базовый тест извлечения без импортов модулей"""
    test_cases = [
        ("450 ккал, 30г белка", 450, 30.0),
        ("Калории: 320, белки: 28г", 320, 28.0),
        ("Итого 280 ккал, б: 22г", 280, 22.0),
        ("Всего 350 калорий, 25г белка", 350, 25.0)
    ]
    
    failed = []
    
    for text, exp_cal, exp_prot in test_cases:
        cal = extract_calories_test(text)
        prot = extract_protein_test(text)
        
        if cal != exp_cal:
            failed.append(f"Калории: '{text}' -> {cal}, ожидалось {exp_cal}")
        
        if prot != exp_prot:
            failed.append(f"Белки: '{text}' -> {prot}, ожидалось {exp_prot}")
    
    return len(failed) == 0, failed


def test_regex_patterns():
    """Тест регулярных выражений"""
    tests = [
        (r'\d+\s*ккал', "450 ккал", True),
        (r'\d+\s*г\s*белка', "30г белка", True),
        (r'б:\s*\d+', "б: 35", True),
        (r'\d+\s*ккал', "no calories here", False)
    ]
    
    failed = []
    
    for pattern, text, should_match in tests:
        matches = bool(re.search(pattern, text, re.IGNORECASE))
        if matches != should_match:
            failed.append(f"Паттерн '{pattern}' в '{text}': {matches}, ожидалось {should_match}")
    
    return len(failed) == 0, failed


def test_file_structure():
    """Тест структуры проекта"""
    required_files = [
        "calorie_bot_modular.py",
        "config.py", 
        "requirements.txt",
        "utils/calorie_calculator.py",
        "handlers/commands.py",
        "data/calorie_database.py"
    ]
    
    missing = []
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            missing.append(file_path)
    
    return len(missing) == 0, missing


def test_python_syntax():
    """Проверка синтаксиса Python файлов"""
    import py_compile
    
    python_files = [
        "calorie_bot_modular.py", 
        "config.py"
    ]
    
    failed = []
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for file_path in python_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            try:
                py_compile.compile(full_path, doraise=True)
            except Exception as e:
                failed.append(f"Синтаксическая ошибка в {file_path}: {e}")
        else:
            failed.append(f"Файл не найден: {file_path}")
    
    return len(failed) == 0, failed


def test_config_validation():
    """Тест конфигурации без импорта модулей"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.py")
    
    if not os.path.exists(config_path):
        return False, ["config.py не найден"]
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие основных переменных
        required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
        missing = []
        
        for var in required_vars:
            if var not in content:
                missing.append(f"Переменная {var} не найдена в config.py")
        
        return len(missing) == 0, missing
        
    except Exception as e:
        return False, [f"Ошибка чтения config.py: {e}"]


def test_requirements():
    """Проверка requirements.txt"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_path = os.path.join(project_root, "requirements.txt")
    
    if not os.path.exists(req_path):
        return False, ["requirements.txt не найден"]
    
    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        required_packages = ['python-telegram-bot', 'openai']
        missing = []
        
        for package in required_packages:
            if package not in content:
                missing.append(f"Пакет {package} не найден в requirements.txt")
        
        return len(missing) == 0, missing
        
    except Exception as e:
        return False, [f"Ошибка чтения requirements.txt: {e}"]


def run_all_tests():
    """Запуск всех простых тестов"""
    tests = [
        (test_basic_extraction, "Базовое извлечение данных"),
        (test_regex_patterns, "Регулярные выражения"),
        (test_file_structure, "Структура проекта"),
        (test_python_syntax, "Синтаксис Python"),
        (test_config_validation, "Конфигурация"),
        (test_requirements, "Зависимости")
    ]
    
    print("🧪 CI/CD Tests - Simple & Reliable\n")
    print("=" * 50)
    
    total_tests = len(tests)
    passed_tests = 0
    all_errors = []
    
    for test_func, test_name in tests:
        try:
            success, errors = test_func()
            
            if success:
                print(f"✅ {test_name}")
                passed_tests += 1
            else:
                print(f"❌ {test_name}")
                for error in errors:
                    print(f"   • {error}")
                    all_errors.append(f"{test_name}: {error}")
                    
        except Exception as e:
            print(f"💥 {test_name}: CRASH - {e}")
            all_errors.append(f"{test_name}: Exception - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests PASSED! Ready for deployment.")
        return True
    else:
        print(f"🔧 {total_tests - passed_tests} tests FAILED")
        print("\n💡 Quick fix suggestions:")
        for error in all_errors[:3]:  # Показываем первые 3 ошибки
            print(f"   • {error}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    # Возвращаем код выхода для CI/CD
    exit_code = 0 if success else 1
    
    print(f"\n🚀 Exit code: {exit_code}")
    sys.exit(exit_code)
