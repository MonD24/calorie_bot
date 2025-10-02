# Тесты для Calorie Bot

Эта директория содержит все тесты для проекта калорийного бота.

## Структура тестов

### Основные тесты (для CI/CD)

- **test_simple.py** - Простые базовые тесты
- **test_smoke.py** - Smoke тесты основных функций
- **test_validation.py** - Тесты валидации данных
- **test_bju_extraction.py** - Тесты извлечения БЖУ из текста
- **test_ci.py** - Специальные тесты для CI окружения

### Специализированные тесты

- **test_photo_analysis.py** - Тесты анализа фотографий еды
- **test_enhanced_validation.py** - Расширенные тесты валидации
- **test_description_extract.py** - Тесты извлечения описаний из текста
- **test_description_processing.py** - Тесты обработки описаний блюд

### Отладочные тесты

- **test_validation_debug.py** - Отладочные тесты валидации с логированием
- **test_real_case.py** - Тесты на реальных кейсах
- **test_morning_weight.py** - Тесты утреннего взвешивания
- **test_morning_weight_flow.py** - Проверка исправлений в коде

## Запуск тестов

### Локально

Запустить все тесты:
```bash
pytest tests/
```

Запустить конкретный тест:
```bash
pytest tests/test_simple.py -v
```

Запустить с покрытием кода:
```bash
pytest tests/ --cov=. --cov-report=html
```

### В CI/CD (GitHub Actions)

Тесты автоматически запускаются при:
- Push в ветки `main`, `beer-fix`, `develop`
- Создании Pull Request в `main`
- Ручном запуске через GitHub UI (workflow_dispatch)

Тесты выполняются на Python 3.10, 3.11 и 3.12.

## Структура тестов

### Mock данные

Файл `mock_gpt.py` содержит моки для GPT API, используемые в тестах.

### Требования

Тесты требуют зависимости из:
- `requirements.txt` - основные зависимости
- `requirements-dev.txt` - тестовые зависимости (pytest, pytest-cov, etc.)

## Добавление новых тестов

1. Создайте файл с именем `test_*.py`
2. Используйте pytest fixtures и conventions
3. Добавьте docstring с описанием тестов
4. Убедитесь, что тесты проходят локально
5. Коммитьте и пушьте - тесты запустятся автоматически

## Отладка

Для детального логирования при отладке:
```bash
pytest tests/test_validation_debug.py -v -s
```

Флаг `-s` отключает перехват вывода pytest.
