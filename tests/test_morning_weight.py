# -*- coding: utf-8 -*-
"""
Тест утреннего запроса веса
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from utils.user_data import get_user_weights, save_user_weights, get_all_users
import datetime


def test_weight_storage():
    """Тестируем сохранение и чтение веса"""
    print("=== ТЕСТ СОХРАНЕНИЯ ВЕСА ===\n")
    
    # Получаем всех пользователей
    users = get_all_users()
    print(f"Найдено пользователей: {len(users)}")
    
    if not users:
        print("❌ Нет пользователей для тестирования")
        return
    
    # Берем первого пользователя для теста
    test_user = users[0]
    print(f"\nТестируем с пользователем: {test_user}")
    
    # Получаем текущие веса
    weights = get_user_weights(test_user)
    print(f"\nТекущие веса: {weights}")
    
    # Добавляем тестовый вес на сегодня
    today = datetime.date.today().isoformat()
    test_weight = 75.5
    
    weights[today] = test_weight
    save_user_weights(test_user, weights)
    print(f"\n✅ Сохранили тестовый вес: {test_weight} кг на {today}")
    
    # Проверяем, что вес сохранился
    weights_check = get_user_weights(test_user)
    if today in weights_check and weights_check[today] == test_weight:
        print(f"✅ Вес успешно прочитан: {weights_check[today]} кг")
    else:
        print(f"❌ Ошибка! Вес не сохранился или не совпадает")
        print(f"Ожидалось: {test_weight}, получено: {weights_check.get(today)}")
    
    print(f"\nВсе веса пользователя:")
    for date, weight in sorted(weights_check.items()):
        print(f"  {date}: {weight} кг")


if __name__ == "__main__":
    test_weight_storage()
