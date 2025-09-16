#!/usr/bin/env python3
"""
Моки для тестирования без реальных API вызовов к GPT
"""

import re
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock


class MockGPTResponses:
    """Класс с предопределенными ответами GPT для тестирования"""
    
    # Типичные ответы GPT на анализ фотографий
    PHOTO_RESPONSES = {
        "творог_банан": """Творог с нарезанным бананом и арахисовой пастой.

Расчет:
- Творог 9% 150г: 160*1.5 = 240 ккал, 16*1.5 = 24г белка, 9*1.5 = 13.5г жира, 2*1.5 = 3г углеводов
- Банан средний 100г: 90 ккал, 1.5г белка, 0.3г жира, 23г углеводов  
- Арахисовая паста ~20г: 600*0.2 = 120 ккал, 25*0.2 = 5г белка, 50*0.2 = 10г жира, 20*0.2 = 4г углеводов

Итого: 450 ккал, 30.5 г белка, 23.8 г жиров, 30 г углеводов""",

        "омлет": """Омлет из двух яиц с сыром и помидорами.

Расчет:
- Яйца 2 шт (120г): 155 ккал, 12г белка, 11г жира, 1г углеводов
- Сыр 30г: 110 ккал, 7г белка, 9г жира, 0г углеводов  
- Помидор 50г: 10 ккал, 0.5г белка, 0г жира, 2г углеводов
- Масло для жарки: 50 ккал, 0г белка, 6г жира, 0г углеводов

Итого: 325 ккал, 19.5 г белка, 26 г жиров, 3 г углеводов""",

        "салат_курица": """Салат с куриной грудкой, овощами и заправкой.

Расчет:
- Куриная грудка 100г: 165 ккал, 31г белка, 3.6г жира, 0г углеводов
- Листья салата 50г: 8 ккал, 0.7г белка, 0г жира, 1.5г углеводов
- Огурцы 80г: 13 ккал, 0.6г белка, 0г жира, 3г углеводов
- Помидоры 60г: 11 ккал, 0.5г белка, 0г жира, 2.4г углеводов  
- Оливковое масло 1 ст.л.: 120 ккал, 0г белка, 14г жира, 0г углеводов

Итого: 317 ккал, 32.8 г белка, 17.6 г жиров, 6.9 г углеводов""",

        "неправильный_ответ": """На фото творог с бананом. Калории: 159 ккал, белки: 32.5г, жиры: 26.4г, углеводы: 29.2г""",
    }
    
    # Ответы на текстовые запросы о еде
    TEXT_RESPONSES = {
        "гречка котлета": "Гречневая каша с мясной котлетой. Итого: 480 ккал, 35 г белка, 16 г жиров, 45 г углеводов",
        "борщ": "Борщ с мясом и сметаной. Всего: 350 ккал, 25 г белка, 10 г жиров, 20 г углеводов", 
        "рис курица": "Рис отварной с куриным филе и овощами. Калории: 420, белок: 32г, жиры: 8г, углеводы: 55г"
    }


def mock_gpt_analyze_photo(image_base64: str) -> Dict[str, Any]:
    """
    Мок для analyze_food_photo без реальных API вызовов
    """
    # Эмулируем разные случаи на основе "содержимого" изображения
    if "error" in image_base64:
        return {"error": "Не удалось проанализировать изображение"}
    
    if "question" in image_base64:
        return {"question": "Можете уточнить размер порции?"}
    
    # По умолчанию возвращаем стандартный ответ для творога с бананом
    response = MockGPTResponses.PHOTO_RESPONSES["творог_банан"]
    
    return {
        "description": "Творог с бананом и арахисовой пастой",
        "calories": 450,
        "protein": 30.5,
        "fat": 23.8, 
        "carbs": 30.0,
        "success": True
    }


def mock_ask_gpt(messages: List[Dict]) -> str:
    """
    Мок для ask_gpt без реальных API вызовов
    """
    # Анализируем сообщения чтобы понять что тестируется
    if messages and len(messages) > 0:
        content = str(messages[0].get('content', ''))
        
        # Если это анализ фото (есть image_url)
        if isinstance(messages[0].get('content'), list):
            for item in messages[0]['content']:
                if item.get('type') == 'image_url':
                    return MockGPTResponses.PHOTO_RESPONSES["творог_банан"]
        
        # Текстовые запросы
        content_lower = content.lower()
        if 'гречка' in content_lower and 'котлета' in content_lower:
            return MockGPTResponses.TEXT_RESPONSES["гречка котлета"]
        elif 'борщ' in content_lower:
            return MockGPTResponses.TEXT_RESPONSES["борщ"]
        elif 'рис' in content_lower and 'курица' in content_lower:
            return MockGPTResponses.TEXT_RESPONSES["рис курица"]
    
    # Дефолтный ответ
    return "Тестовое блюдо. Итого: 300 ккал, 20 г белка, 10 г жиров, 25 г углеводов"


class MockGPTContext:
    """Контекст-менеджер для подмены GPT вызовов в тестах"""
    
    def __init__(self, photo_response_key: str = "творог_банан"):
        self.photo_response_key = photo_response_key
        self.patches = []
    
    def __enter__(self):
        # Патчим функции которые вызывают GPT
        from unittest.mock import patch
        
        # Основной мок для ask_gpt
        ask_gpt_patch = patch('utils.calorie_calculator.ask_gpt', side_effect=mock_ask_gpt)
        self.patches.append(ask_gpt_patch)
        ask_gpt_patch.start()
        
        # Мок для analyze_food_photo
        photo_patch = patch('utils.photo_processor.ask_gpt', side_effect=mock_ask_gpt)  
        self.patches.append(photo_patch)
        photo_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Останавливаем все патчи
        for patch_obj in self.patches:
            patch_obj.stop()


# Удобные декораторы для тестов
def with_mock_gpt(photo_response: str = "творог_банан"):
    """
    Декоратор для тестов с мокированным GPT
    
    Usage:
    @with_mock_gpt("омлет")  
    def test_something():
        ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with MockGPTContext(photo_response):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_mock_response(key: str) -> str:
    """Получить мок-ответ по ключу"""
    return MockGPTResponses.PHOTO_RESPONSES.get(key) or MockGPTResponses.TEXT_RESPONSES.get(key, "")


if __name__ == "__main__":
    # Демонстрация работы моков
    print("🧪 Демонстрация мок-ответов GPT:")
    print()
    
    print("📸 Фото творога с бананом:")
    print(MockGPTResponses.PHOTO_RESPONSES["творог_банан"])
    print()
    
    print("💬 Текстовый запрос:")
    print(mock_ask_gpt([{"content": "Сколько калорий в гречке с котлетой?"}]))
    print()
    
    print("✅ Моки готовы к использованию!")
