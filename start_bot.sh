#!/bin/bash
# Простой скрипт запуска бота

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BOT_DIR"

echo "🚀 Запуск калорийного бота..."

# Проверяем наличие виртуального окружения
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
fi

# Проверяем наличие основного файла
if [ ! -f "calorie_bot_modular.py" ]; then
    echo "❌ Файл calorie_bot_modular.py не найден!"
    exit 1
fi

# Запускаем бота
echo "▶️  Запуск бота..."
python3 calorie_bot_modular.py