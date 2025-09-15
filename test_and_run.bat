@echo off
chcp 65001 >nul
echo 🔧 Тестирование исправлений...

cd /d "%~dp0"

REM Активируем виртуальную среду
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Виртуальная среда не найдена!
    pause
    exit /b 1
)

REM Останавливаем все процессы с ботом
echo 🛑 Остановка старых процессов...
taskkill /F /IM python.exe /FI "COMMANDLINE eq *calorie_bot*" 2>nul

REM Ждем
timeout /t 3 /nobreak >nul

REM Проверяем синтаксис
echo 📋 Проверка синтаксиса...
python -m py_compile calorie_bot_modular.py
if %errorlevel% neq 0 (
    echo ❌ Ошибки синтаксиса!
    pause
    exit /b 1
)

echo ✅ Синтаксис OK

REM Тестируем импорты
echo 📦 Проверка импортов...
python -c "
try:
    import handlers.commands
    import handlers.text_handler
    import handlers.photo_handler
    import handlers.callback_handler
    print('✅ Импорты OK')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

if %errorlevel% neq 0 (
    echo ❌ Ошибки импортов!
    pause
    exit /b 1
)

echo ✅ Все проверки пройдены!
echo 🚀 Запуск бота...

REM Запускаем бота
python calorie_bot_modular.py
