#!/bin/bash
# Сервисный скрипт для управления ботом

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$BOT_DIR/bot.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Бот уже запущен (PID: $PID)"
                exit 0
            fi
        fi
        
        cd "$BOT_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        nohup python3 calorie_bot_modular.py > bot.log 2>&1 &
        echo $! > "$PID_FILE"
        echo "Бот запущен (PID: $!)"
        ;;
    
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "Бот остановлен"
            else
                echo "Процесс не найден"
                rm -f "$PID_FILE"
            fi
        else
            echo "PID файл не найден"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Бот запущен (PID: $PID)"
            else
                echo "PID файл найден, но процесс не запущен"
            fi
        else
            echo "Бот не запущен"
        fi
        ;;
    
    *)
        echo "Использование: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac