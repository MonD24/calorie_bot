# -*- coding: utf-8 -*-
"""
Утилиты для работы с пользовательскими данными
"""
import os
import json
import logging
import traceback
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
            # Проверяем что данные можно сериализовать
            data_to_save = user_data.get(data_type, {})

            # Валидация данных перед сохранением
            if data_type == 'food_log':
                data_to_save = _validate_food_log_data(data_to_save)

            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Сначала пробуем сериализовать в память
            try:
                json_str = json.dumps(data_to_save, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                logging.error(f"JSON serialization error for {data_type} (user {user_id}): {e}")
                logging.error(f"Problematic data: {data_to_save}")
                continue

            # Сохраняем во временный файл, затем переименовываем
            temp_file_path = file_path + '.tmp'
            try:
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                    f.flush()  # Принудительно записываем на диск
                    os.fsync(f.fileno())  # Синхронизируем с диском

                # Атомарно заменяем старый файл
                if os.path.exists(file_path):
                    os.replace(temp_file_path, file_path)
                else:
                    os.rename(temp_file_path, file_path)

                logging.debug(f"Successfully saved {data_type} for user {user_id}")

            except OSError as e:
                logging.error(f"File system error saving {data_type} for user {user_id}: {e}")
                # Удаляем временный файл если остался
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass

        except Exception as e:
            logging.error(f"Unexpected error saving {data_type} for user {user_id}: {e}")
            logging.error(f"Data type: {type(user_data.get(data_type))}")
            if hasattr(e, '__traceback__'):
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")


def _validate_food_log_data(food_log_data: Any) -> Dict[str, list]:
    """Валидация и очистка данных food_log"""
    if not isinstance(food_log_data, dict):
        logging.warning(f"food_log_data is not dict: {type(food_log_data)}")
        return {}

    validated_data = {}

    for date_str, foods in food_log_data.items():
        if not isinstance(date_str, str):
            logging.warning(f"Invalid date key: {date_str} (type: {type(date_str)})")
            continue

        if not isinstance(foods, list):
            logging.warning(f"Foods for date {date_str} is not list: {type(foods)}")
            continue

        validated_foods = []
        for food_entry in foods:
            if not isinstance(food_entry, list):
                logging.warning(f"Food entry is not list: {food_entry}")
                continue

            if len(food_entry) < 2:
                logging.warning(f"Food entry too short: {food_entry}")
                continue

            # Валидируем название блюда
            food_name = food_entry[0]
            if not isinstance(food_name, str):
                logging.warning(f"Invalid food name: {food_name}")
                continue

            # Валидируем калории
            try:
                calories = food_entry[1]
                if calories is None:
                    logging.warning(f"Calories is None for {food_name}")
                    continue

                calories = float(calories)
                if not (0 <= calories <= 10000):  # Разумные пределы
                    logging.warning(f"Calories out of range: {calories} for {food_name}")
                    continue

                # Проверяем на специальные значения
                if not (calories == calories):  # NaN check
                    logging.warning(f"Calories is NaN for {food_name}")
                    continue

                if calories == float('inf') or calories == float('-inf'):
                    logging.warning(f"Calories is infinite for {food_name}")
                    continue

            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid calories for {food_name}: {food_entry[1]} ({e})")
                continue

            # Валидируем белок (если есть)
            protein = None
            if len(food_entry) >= 3 and food_entry[2] is not None:
                try:
                    protein = float(food_entry[2])
                    if not (0 <= protein <= 1000):  # Разумные пределы
                        logging.warning(f"Protein out of range: {protein} for {food_name}")
                        protein = None
                    elif not (protein == protein):  # NaN check
                        logging.warning(f"Protein is NaN for {food_name}")
                        protein = None
                    elif protein == float('inf') or protein == float('-inf'):
                        logging.warning(f"Protein is infinite for {food_name}")
                        protein = None
                except (ValueError, TypeError):
                    logging.warning(f"Invalid protein for {food_name}: {food_entry[2]}")
                    protein = None

            # Добавляем валидированную запись
            validated_entry = [food_name, int(calories)]  # Округляем калории до целого
            if protein is not None:
                validated_entry.append(int(protein))  # Округляем белок до целого

            validated_foods.append(validated_entry)

        if validated_foods:  # Добавляем только если есть валидные записи
            validated_data[date_str] = validated_foods

    return validated_data


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
    try:
        logging.debug(f"🍽️ Сохраняем food_log для пользователя {user_id}")
        logging.debug(f"Данные: {food_log}")

        user_data = load_user_data(user_id)
        user_data['food_log'] = food_log
        save_user_data(user_id, user_data)

        logging.info(f"✅ Food_log успешно сохранен для пользователя {user_id}")

    except Exception as e:
        logging.error(f"❌ Ошибка сохранения food_log для пользователя {user_id}: {e}")
        logging.error(f"Тип данных food_log: {type(food_log)}")
        logging.error(f"Размер данных: {len(str(food_log))} символов")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise e  # Пробрасываем ошибку выше


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
