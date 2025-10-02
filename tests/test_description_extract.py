#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест извлечения описания из ответа GPT
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.photo_processor import extract_description_from_photo_response

def test_description_extraction():
    """Тестируем извлечение описания с детальными ингредиентами"""
    
    print("🧪 ТЕСТ ИЗВЛЕЧЕНИЯ ОПИСАНИЯ БЛЮДА")
    print("=" * 50)
    
    # Тест 1: Правильный формат с детальным описанием
    response1 = """На фото куриное блюдо с гарниром: жареная куриная грудка, отварной рис, вареное яйцо, маринованные огурцы, болгарский перец

📊 ШАГ 2 - РАСЧЕТ КАЖДОГО ИНГРЕДИЕНТА:
Куриная грудка жареная ~120г: 165×1.2×1.2 = 238 ккал, 37г белка, 5г жиров
Рис отварной ~100г: 116×1.0 = 116 ккал, 2.2г белка, 0.5г жиров, 23г углеводов
Яйцо вареное ~50г: 155×0.5 = 78 ккал, 6.5г белка, 5.5г жиров

ИТОГО: 432 ккал, 45.7 г белка, 11 г жиров, 25 г углеводов"""
    
    description1 = extract_description_from_photo_response(response1)
    print(f"Тест 1 - Результат: '{description1}'")
    print("✅ Ожидаемо: детальное перечисление ингредиентов")
    
    # Тест 2: Описание без "На фото"
    response2 = """Куриное блюдо с овощами и рисом
    
📊 ШАГ 2 - РАСЧЕТ:
Куриная грудка ~100г: 165 ккал
ИТОГО: 165 ккал"""
    
    description2 = extract_description_from_photo_response(response2)
    print(f"\nТест 2 - Результат: '{description2}'")
    
    # Тест 3: Описание с техническими символами
    response3 = """📋 На фото домашнее куриное блюдо: курица, рис, яйцо, соленые огурцы
    
📊 Расчет калорий..."""
    
    description3 = extract_description_from_photo_response(response3)
    print(f"\nТест 3 - Результат: '{description3}'")
    
    print("\n" + "=" * 50)
    print("🎯 ПРОВЕРКА: Все описания должны содержать детальный список ингредиентов")

if __name__ == "__main__":
    test_description_extraction()
