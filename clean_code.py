#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической очистки кода от пробелов
"""

import os
import re
from pathlib import Path

def clean_file(file_path):
    """Очищает файл от лишних пробелов"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Убираем завершающие пробелы в строках
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Убираем лишние пустые строки в конце файла
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        cleaned_content = '\n'.join(cleaned_lines) + '\n'
        
        # Записываем только если есть изменения
        if content != cleaned_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Очищен: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return False

def clean_python_files():
    """Очищает все Python файлы в проекте"""
    project_root = Path(__file__).parent
    
    # Папки для очистки
    folders = ['utils', 'handlers', 'data']
    
    cleaned_count = 0
    for folder in folders:
        folder_path = project_root / folder
        if folder_path.exists():
            for py_file in folder_path.glob('*.py'):
                if clean_file(py_file):
                    cleaned_count += 1
    
    print(f"\nОчищено файлов: {cleaned_count}")
    return cleaned_count

if __name__ == "__main__":
    print("🧹 ОЧИСТКА КОДА ОТ ЛИШНИХ ПРОБЕЛОВ")
    print("=" * 40)
    
    cleaned = clean_python_files()
    
    if cleaned > 0:
        print("✅ Код успешно очищен!")
    else:
        print("ℹ️ Код уже был чистым")
