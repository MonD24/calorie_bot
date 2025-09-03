# -*- coding: utf-8 -*-
"""
Утилиты для работы с пользовательскими данными
"""
import os
import json
import logging
from typing import Dict, Any

# Исправляем импорт для работы из main.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_DIR


def get_user_files(user_id: str) -> Dict[str, str]:
    """Получаем пути к файлам конкретного пользователя"""
    user_dir = os.path.join(DATA_DIR, f'user_{user_id}')
    os.makedirs(user_dir, exist_ok=True)

    return {
        'profile': os.path.join(user_dir, 'profile.json'),
        'diary': os.path.join(user_dir, 'diary.json'),
        'weights': os.path.join(user_dir, 'weights.json'),
        'food_log': os.path.join(user_dir, 'food_log.json'),
        'burned': os.path.join(user_dir, 'burned.json')
    }


def load_user_data(user_id: str) -> Dict[str, Any]:
    """Загружаем данные конкретного пользователя"""
    files = get_user_files(user_id)
    user_data = {}

    for data_type, file_path in files.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                user_data[data_type] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data[data_type] = {}
            logging.info(f"Initialized empty {data_type} for user {user_id}")

    return user_data


def save_user_data(user_id: str, user_data: Dict[str, Any]) -> None:
    """Сохраняем данные конкретного пользователя"""
    files = get_user_files(user_id)

    for data_type, file_path in files.items():
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data.get(data_type, {}), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving {data_type} for user {user_id}: {e}")


# Удобные функции для работы с отдельными типами данных
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Получаем профиль пользователя"""
    user_data = load_user_data(user_id)
    return user_data.get('profile', {})


def save_user_profile(user_id: str, profile: Dict[str, Any]) -> None:
    """Сохраняем профиль пользователя"""
    user_data = load_user_data(user_id)
    user_data['profile'] = profile
    save_user_data(user_id, user_data)


def get_user_diary(user_id: str) -> Dict[str, int]:
    """Получаем дневник пользователя"""
    user_data = load_user_data(user_id)
    return user_data.get('diary', {})


def save_user_diary(user_id: str, diary: Dict[str, int]) -> None:
    """Сохраняем дневник пользователя"""
    user_data = load_user_data(user_id)
    user_data['diary'] = diary
    save_user_data(user_id, user_data)


def get_user_weights(user_id: str) -> Dict[str, float]:
    """Получаем веса пользователя"""
    user_data = load_user_data(user_id)
    return user_data.get('weights', {})


def save_user_weights(user_id: str, weights: Dict[str, float]) -> None:
    """Сохраняем веса пользователя"""
    user_data = load_user_data(user_id)
    user_data['weights'] = weights
    save_user_data(user_id, user_data)


def get_user_food_log(user_id: str) -> Dict[str, list]:
    """Получаем лог еды пользователя"""
    user_data = load_user_data(user_id)
    return user_data.get('food_log', {})


def save_user_food_log(user_id: str, food_log: Dict[str, list]) -> None:
    """Сохраняем лог еды пользователя"""
    user_data = load_user_data(user_id)
    user_data['food_log'] = food_log
    save_user_data(user_id, user_data)


def get_user_burned(user_id: str) -> Dict[str, int]:
    """Получаем потраченные калории пользователя"""
    user_data = load_user_data(user_id)
    return user_data.get('burned', {})


def save_user_burned(user_id: str, burned: Dict[str, int]) -> None:
    """Сохраняем потраченные калории пользователя"""
    user_data = load_user_data(user_id)
    user_data['burned'] = burned
    save_user_data(user_id, user_data)


def get_all_users() -> list:
    """Получаем список всех пользователей"""
    if not os.path.exists(DATA_DIR):
        return []
    
    users = []
    for user_dir in os.listdir(DATA_DIR):
        if user_dir.startswith('user_'):
            user_id = user_dir[5:]  # убираем префикс 'user_'
            users.append(user_id)
    
    return users
