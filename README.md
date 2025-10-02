# �️ Fat Helper - Telegram бот для подсчета калорий

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Telegram](https://img.shields.io/badge/telegram-bot-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT4--Vision-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://github.com/MonD24/calorie_bot/workflows/Tests/badge.svg)

Умный Telegram-бот для контроля калорий с ИИ-анализом фотографий еды и персональными рекомендациями.

## ⚡ Быстрый старт

**📋 [QUICKSTART.md](QUICKSTART.md) - Начните за 2 минуты!**

## 🌟 Возможности

### � ИИ-анализ фотографий
- **GPT-4 Vision API** для точного распознавания блюд
- Автоматический подсчет **калорий, белков, жиров, углеводов**
- Распознавание **множественных блюд** на одном фото
- Определение **размера порций** и веса продуктов

### ✍️ Гибкий текстовый ввод
- **"Съел борщ"** - бот уточнит детали  
- **"Борщ, 350 ккал"** - мгновенное добавление
- **"100г гречки + 200г курицы"** - детальный анализ
- База из **500+ популярных продуктов**

### 🎯 Персональные цели
- **Автоматический расчет** нормы калорий (Mifflin-St Jeor)
- **3 режима**: похудение (-500 ккал), поддержание, набор массы (+300 ккал)
- **Кастомные лимиты** калорий (800-5000 ккал/день)
- **Трекинг веса** с историей изменений

### 📊 Умный дневник питания
- Подробная **история всех приемов пищи**
- **Прогресс по дням** с общим БЖУ
- **Остаток калорий** в реальном времени
- **Уведомления** о превышении лимита

## 🚀 Установка

### 🐧 Linux/macOS (Автоматически)
```bash
git clone https://github.com/yourusername/calorie-bot.git
cd calorie-bot
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### 🪟 Windows
```bash
git clone https://github.com/yourusername/calorie-bot.git
cd calorie-bot
test_and_run.bat
```

### 🔧 Ручная установка
```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка .env файла
echo "TELEGRAM_BOT_TOKEN=your_bot_token" > .env
echo "OPENAI_API_KEY=your_openai_key" >> .env

# 3. Запуск
python calorie_bot_modular.py
```

## 📱 Команды

| Команда | Описание |
|---------|----------|
| `/start` | 🚀 **Регистрация и настройка профиля** |
| `/goal` | 🎯 **Смена цели** (похудение/поддержание/набор) |
| `/limit 2000` | ⚡ **Кастомный лимит калорий** (800-5000) |
| `/left` | 📊 **Остаток калорий** на сегодня |
| `/food` | 📋 **Дневник питания** с БЖУ |
| `/weight 70` | ⚖️ **Обновить вес** для пересчета нормы |

## 🧠 Как использовать

### 📸 Отправьте фото еды
```
👆 [ФОТО БОРЩА]
🤖 "Обнаружен борщ украинский с мясом, примерно 300г
    Калории: 210 ккал | Б: 12г | Ж: 8г | У: 20г
    Добавить в дневник?"
```

### ✍️ Опишите текстом
```
👤 "Съел шаурму"
🤖 "Какого размера была шаурма? (маленькая/средняя/большая)"

👤 "Шаурма, 650 ккал"  
🤖 "✅ Добавлено: Шаурма (650 ккал)"
```

## 🏗️ Архитектура

```
📂 calorie_bot/
├── 🚀 calorie_bot_modular.py     # Главный файл
├── ⚙️ config.py                  # Конфигурация
├── 📁 handlers/                  # Обработчики
│   ├── commands.py               # Команды (/start, /goal, etc)
│   ├── text_handler.py           # Парсинг текста + регистрация
│   ├── photo_handler.py          # GPT-4 Vision анализ
│   └── callback_handler.py       # Inline кнопки
├── 📁 utils/                     # Утилиты
│   ├── calorie_calculator.py     # BMR/TDEE расчеты
│   ├── photo_processor.py        # Обработка изображений
│   └── user_data.py              # JSON хранилище
├── 📁 data/                      # База данных
│   └── calorie_database.py       # 500+ продуктов
└── 📄 user_data/                 # Пользовательские данные
    ├── profiles.json             # Профили пользователей
    ├── diary_entries.json        # Дневники питания
    └── food_logs.json            # Логи всех приемов пищи
```

## � Безопасность & Приватность

- 🔑 **API ключи** только в переменных окружения
- 💾 **Локальное хранение** данных (без внешних БД)
- 🛡️ **Безопасная передача** изображений через OpenAI API
- 🔄 **Автоматические бэкапы** пользовательских данных

## 📈 Производительность

- ⚡ **< 3 сек** анализ фото через GPT-4 Vision
- 💾 **< 1 МБ** на пользователя в год
- 🔄 **Автоперезапуск** при сбоях
- 📊 **Ротация логов** для экономии места

## 🐛 Диагностика

```bash
# Просмотр логов
./setup_and_run.sh logs

# Проверка статуса  
./setup_and_run.sh status

# Перезапуск бота
./setup_and_run.sh restart

# Остановка
./setup_and_run.sh stop
```

## � Требования

- **Python 3.8+**
- **Telegram Bot Token** ([создать бота](https://t.me/BotFather))
- **OpenAI API Key** ([получить ключ](https://platform.openai.com))
- **~$5/мес** на OpenAI API (при умеренном использовании)

## � Changelog

**v1.0.0** - Полный релиз
- ✅ Анализ фото через GPT-4 Vision  
- ✅ Ручной ввод калорий + автопарсинг
- ✅ Персональные цели и кастомные лимиты
- ✅ База из 500+ продуктов
- ✅ Кроссплатформенные скрипты установки

[Полный CHANGELOG.md](CHANGELOG.md)

## � Тестирование

Все тесты находятся в директории `tests/` и автоматически запускаются в GitHub Actions.

### Локальный запуск

**Windows:**
```bash
run_tests.bat
```

**Linux/macOS:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Или напрямую через pytest:**
```bash
# Все тесты
pytest tests/ -v

# Конкретный тест
pytest tests/test_simple.py -v

# С покрытием кода
pytest tests/ --cov=. --cov-report=html
```

### CI/CD

Тесты автоматически запускаются при:
- Push в ветки `main`, `beer-fix`, `develop`
- Создании Pull Request
- Ручном запуске через GitHub Actions

Подробнее: [tests/README.md](tests/README.md)

## �🤝 Участие в разработке

Читайте [CONTRIBUTING.md](CONTRIBUTING.md) для инструкций по участию.

## 📄 Лицензия

MIT License - подробности в [LICENSE](LICENSE)

---

⭐ **Понравился проект? Поставьте звезду!**  
🐛 **Нашли баг?** [Создайте issue](https://github.com/yourusername/calorie-bot/issues)  
💡 **Есть идея?** [Обсудим в Discussions](https://github.com/yourusername/calorie-bot/discussions)
