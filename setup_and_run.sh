#!/bin/bash

# Единый скрипт установки и запуска калорийного бота
# Использование: ./setup_and_run.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII лого
echo -e "${CYAN}"
cat << "EOF"
  ____      _            _        ____        _   
 / ___|__ _| | ___  _ __(_) ___  | __ )  ___ | |_ 
| |   / _` | |/ _ \| '__| |/ _ \ |  _ \ / _ \| __|
| |__| (_| | | (_) | |  | |  __/ | |_) | (_) | |_ 
 \____\__,_|_|\___/|_|  |_|\___| |____/ \___/ \__|
                                                  
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 Установка и запуск калорийного Telegram бота${NC}"
echo

# Настройки
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/bot.log"
PID_FILE="$PROJECT_DIR/bot.pid"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Функция остановки бота
stop_bot() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Остановка бота (PID: $pid)..."
            kill "$pid"
            rm -f "$PID_FILE"
            sleep 2
        fi
    fi
    
    # Убиваем все процессы Python с main.py
    pkill -f "python.*main.py" 2>/dev/null || true
    
    log "Бот остановлен"
}

# Проверка системы
check_system() {
    log "Проверка системы..."
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 не найден!"
        info "Установите Python 3:"
        info "  sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        success "Python $PYTHON_VERSION - OK"
    else
        error "Требуется Python 3.8+, найден: $PYTHON_VERSION"
        exit 1
    fi
    
    # Проверяем pip
    if ! python3 -m pip --version &>/dev/null; then
        error "pip не найден!"
        info "Установите pip: sudo apt install -y python3-pip"
        exit 1
    fi
    
    # Проверяем venv
    if ! python3 -m venv --help &>/dev/null; then
        error "python3-venv не найден!"
        info "Установите venv: sudo apt install -y python3-venv"
        exit 1
    fi
}

# Создание виртуального окружения
setup_venv() {
    log "Настройка виртуального окружения..."
    
    if [[ -d "$VENV_DIR" ]]; then
        warning "Виртуальное окружение уже существует, пересоздаём..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Обновляем pip
    pip install --upgrade pip
    
    success "Виртуальное окружение создано"
}

# Установка зависимостей
install_dependencies() {
    log "Установка зависимостей..."
    
    source "$VENV_DIR/bin/activate"
    
    if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
        pip install -r "$PROJECT_DIR/requirements.txt"
    else
        warning "requirements.txt не найден, устанавливаем базовые зависимости..."
        pip install python-telegram-bot[job-queue] openai aiohttp python-dotenv
    fi
    
    # Проверяем и обновляем OpenAI API
    log "Проверка OpenAI API..."
    if python3 check_openai.py; then
        success "OpenAI API настроен корректно"
    else
        warning "Проблемы с OpenAI API, но продолжаем..."
    fi
    
    success "Зависимости установлены"
}

# Настройка конфигурации
setup_config() {
    log "Настройка конфигурации..."
    
    # Создаем .env из примера если его нет
    if [[ ! -f "$PROJECT_DIR/.env" ]] && [[ -f "$PROJECT_DIR/.env.example" ]]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        warning "Создан файл .env из примера"
        warning "⚠️  ОБЯЗАТЕЛЬНО отредактируйте .env и укажите ваши API ключи!"
    fi
    
    # Создаем директории
    mkdir -p "$PROJECT_DIR/bot_data" "$PROJECT_DIR/logs"
    
    # Проверяем конфигурацию
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
    if TELEGRAM_BOT_TOKEN and OPENAI_API_KEY:
        if len(TELEGRAM_BOT_TOKEN) > 10 and len(OPENAI_API_KEY) > 10:
            print('OK')
        else:
            print('ERROR: Короткие токены')
            sys.exit(1)
    else:
        print('ERROR: Токены не настроены')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>/dev/null; then
        success "Конфигурация корректна"
    else
        warning "Проблемы с конфигурацией"
        warning "Проверьте токены в файле .env или config.py"
    fi
}

# Тестирование импортов
test_imports() {
    log "Тестирование импортов..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    if python3 test_imports.py 2>/dev/null | grep -q "Все тесты пройдены"; then
        success "Импорты работают корректно"
    else
        warning "Есть проблемы с импортами, но пробуем запустить..."
    fi
}

# Запуск бота через nohup
start_bot() {
    log "Запуск бота в фоновом режиме..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    # Запускаем через nohup
    nohup python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
import main
main.main()
" > "$LOG_FILE" 2>&1 &
    
    # Сохраняем PID
    echo $! > "$PID_FILE"
    
    local pid=$(cat "$PID_FILE")
    success "Бот запущен в фоне (PID: $pid)"
    info "Логи: $LOG_FILE"
    info "PID файл: $PID_FILE"
}

# Проверка статуса
check_status() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            success "Бот работает (PID: $pid)"
            return 0
        else
            warning "PID файл существует, но процесс не найден"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Проверяем по имени процесса
    if pgrep -f "python.*main.py" >/dev/null; then
        local pid=$(pgrep -f "python.*main.py")
        warning "Бот работает без PID файла (PID: $pid)"
        echo "$pid" > "$PID_FILE"
        return 0
    fi
    
    error "Бот не запущен"
    return 1
}

# Показ логов
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${BLUE}Последние 20 строк логов:${NC}"
        tail -n 20 "$LOG_FILE"
        echo
        info "Для просмотра в реальном времени: tail -f $LOG_FILE"
    else
        warning "Лог файл не найден: $LOG_FILE"
    fi
}

# Главная функция
main() {
    case "${1:-install}" in
        "install"|"")
            log "🔧 Полная установка и запуск..."
            stop_bot
            check_system
            setup_venv
            install_dependencies
            setup_config
            test_imports
            start_bot
            sleep 3
            check_status
            echo
            echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${CYAN}║                    🎉 БОТ УСТАНОВЛЕН И ЗАПУЩЕН!              ║${NC}"
            echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
            ;;
        "start")
            log "🚀 Запуск бота..."
            start_bot
            sleep 2
            check_status
            ;;
        "stop")
            log "🛑 Остановка бота..."
            stop_bot
            ;;
        "restart")
            log "🔄 Перезапуск бота..."
            stop_bot
            sleep 2
            start_bot
            sleep 2
            check_status
            ;;
        "status")
            log "📊 Проверка статуса..."
            check_status
            ;;
        "logs")
            show_logs
            ;;
        "update")
            log "🔄 Обновление зависимостей..."
            source "$VENV_DIR/bin/activate"
            pip install --upgrade pip
            if [[ -f requirements.txt ]]; then
                pip install -r requirements.txt --upgrade
            fi
            log "Перезапуск после обновления..."
            stop_bot
            sleep 2
            start_bot
            ;;
        "fix-openai")
            log "🔧 Исправление OpenAI API..."
            chmod +x fix_openai.sh
            ./fix_openai.sh
            ;;
        *)
            echo "Использование: $0 {install|start|stop|restart|status|logs|update|fix-openai}"
            echo
            echo "Команды:"
            echo "  install     - полная установка и запуск (по умолчанию)"
            echo "  start       - запустить бота"
            echo "  stop        - остановить бота"
            echo "  restart     - перезапустить бота"
            echo "  status      - проверить статус"
            echo "  logs        - показать логи"
            echo "  update      - обновить зависимости и перезапустить"
            echo "  fix-openai  - исправить проблемы с OpenAI API"
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'echo; log "Прервано пользователем"; exit 130' INT TERM

# Запуск
main "$@"
