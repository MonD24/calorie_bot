#!/bin/bash

# Простой скрипт запуска бота

# Автоисправление концов строк
fix_line_endings() {
    local script_path="$0"
    if command -v file >/dev/null && file "$script_path" | grep -q "CRLF"; then
        echo "🔧 Исправляем Windows line endings..."
        sed -i 's/\r$//' "$script_path" 2>/dev/null || tr -d '\r' < "$script_path" > "${script_path}.tmp" && mv "${script_path}.tmp" "$script_path"
        chmod +x "$script_path"
        echo "✅ Исправлено, перезапускаем..."
        exec "$script_path" "$@"
    fi
}

fix_line_endings "$@"

echo "🚀 Запуск калорийного бота..."

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено. Сначала запустите install_linux.sh"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден. Скопируйте .env.example в .env и заполните токены"
    exit 1
fi

# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
echo "▶️ Запуск бота..."
python3 calorie_bot_modular.py
