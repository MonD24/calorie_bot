# Makefile для удобного запуска линтеров и тестов

.PHONY: help install test lint format check-format check-imports security clean all

help: ## Показать помощь
	@echo "🛠️  Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости для разработки
	pip install -r requirements-dev.txt

test: ## Запустить все тесты
	python tests/test_smoke.py
	python tests/test_ci.py

lint: ## Проверить качество кода
	flake8 calorie_bot_modular.py utils/ handlers/ data/
	black --check calorie_bot_modular.py utils/ handlers/ data/
	isort --check-only calorie_bot_modular.py utils/ handlers/ data/

format: ## Автоматически отформатировать код
	black calorie_bot_modular.py utils/ handlers/ data/
	isort calorie_bot_modular.py utils/ handlers/ data/

check-format: ## Проверить форматирование без изменений
	black --check --diff calorie_bot_modular.py utils/ handlers/ data/

check-imports: ## Проверить сортировку импортов
	isort --check-only --diff calorie_bot_modular.py utils/ handlers/ data/

security: ## Проверка безопасности
	bandit -r . -ll

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

all: format lint test ## Выполнить все проверки и тесты
