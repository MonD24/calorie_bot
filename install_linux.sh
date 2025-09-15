#!/bin/bash

# Упрощенный скрипт установки для Linux

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
    # Исправляем все .sh файлы
    for sh_file in *.sh; do
        [[ -f "$sh_file" ]] && command -v file >/dev/null && file "$sh_file" | grep -q "CRLF" && {
            sed -i 's/\r$//' "$sh_file" 2>/dev/null || tr -d '\r' < "$sh_file" > "${sh_file}.tmp" && mv "${sh_file}.tmp" "$sh_file"
            chmod +x "$sh_file"
        }
    done
}

fix_line_endings "$@"

echo "🚀 Установка калорийного бота..."

# Проверка наличия Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Устанавливаем..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Копирование конфигурации
if [ ! -f ".env" ]; then
    echo "⚙️ Создание файла конфигурации..."
    cp .env.example .env
    echo "✅ Файл .env создан. Отредактируйте его и укажите ваши токены:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - OPENAI_API_KEY"
fi

echo "✅ Установка завершена!"
echo ""
echo "Для запуска бота:"
echo "1. Отредактируйте файл .env:"
echo "   nano .env"
echo ""
echo "2. Запустите бота:"
echo "   source venv/bin/activate"
echo "   python3 calorie_bot_modular.py"
