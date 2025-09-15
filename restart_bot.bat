@echo off
echo "🔄 Перезапуск бота..."

REM Переходим в директорию проекта
cd /d "%~dp0"

REM Активируем виртуальную среду
call venv\Scripts\activate.bat

REM Останавливаем все Python процессы с ботом
taskkill /F /IM python.exe /FI "WINDOWTITLE eq calorie_bot*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *calorie_bot_modular.py*" 2>nul

REM Ждем немного
timeout /t 2 /nobreak >nul

REM Запускаем бота
echo "🚀 Запуск бота..."
start /b python calorie_bot_modular.py > bot.log 2>&1

echo "✅ Бот перезапущен!"
echo "📋 Для просмотра логов: type bot.log"
pause
