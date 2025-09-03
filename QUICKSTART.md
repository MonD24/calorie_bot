# 🚀 Быстрый запуск

## 📋 Пошаговая инструкция

### 1. Подготовка
```bash
# Клонирование репозитория
git clone https://github.com/yourusername/calorie-bot.git
cd calorie-bot

# Настройка окружения
chmod +x setup_and_run.sh
./setup_and_run.sh setup
```

### 2. Настройка токенов
```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать файл .env:
nano .env
```

Укажите в .env файле:
- `TELEGRAM_BOT_TOKEN` - получите от [@BotFather](https://t.me/BotFather)
- `OPENAI_API_KEY` - получите на [OpenAI Platform](https://platform.openai.com/api-keys)

### 3. Запуск
```bash
# Запустить бота
./setup_and_run.sh start

# Проверить статус
./setup_and_run.sh status
```

## 🛠 Команды управления

| Команда | Описание |
|---------|----------|
| `./setup_and_run.sh setup` | Настройка окружения |
| `./setup_and_run.sh start` | Запуск бота |
| `./setup_and_run.sh stop` | Остановка бота |
| `./setup_and_run.sh restart` | Перезапуск бота |
| `./setup_and_run.sh status` | Статус бота |
| `./setup_and_run.sh logs` | Просмотр логов |

## 🐛 Устранение проблем

### Ошибки OpenAI
```bash
pip install openai>=1.0.0 --upgrade
```

### Просмотр логов
```bash
./setup_and_run.sh logs
```

### Полный перезапуск
```bash
./setup_and_run.sh stop
./setup_and_run.sh start
```
