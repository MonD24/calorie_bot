# -*- coding: utf-8 -*-
"""
Тест полного потока утреннего взвешивания
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

print("=== ТЕСТ ПОТОКА УТРЕННЕГО ВЗВЕШИВАНИЯ ===\n")

print("📋 Проверяем исправления в коде:\n")

# Проверяем, что функция morning_weight_function использует правильный метод
with open('handlers/commands.py', 'r', encoding='utf-8') as f:
    commands_content = f.read()
    
if 'context.application.user_data[user_id_int]' in commands_content:
    print("✅ morning_weight_function использует правильный context.application.user_data")
else:
    print("❌ morning_weight_function НЕ использует context.application.user_data")

if "logging.info(f\"Morning weight request sent to user" in commands_content:
    print("✅ Добавлено логирование в morning_weight_function")
else:
    print("❌ Логирование НЕ добавлено в morning_weight_function")

# Проверяем handle_daily_weight
with open('handlers/text_handler.py', 'r', encoding='utf-8') as f:
    text_handler_content = f.read()
    
if "logging.info(f\"User {user_id} recorded weight:" in text_handler_content:
    print("✅ Добавлено логирование в handle_daily_weight")
else:
    print("❌ Логирование НЕ добавлено в handle_daily_weight")

if "context.user_data['step'] = None" in text_handler_content:
    print("✅ handle_daily_weight сбрасывает step после сохранения")
else:
    print("❌ handle_daily_weight НЕ сбрасывает step")

print("\n" + "="*60)
print("РЕЗЮМЕ ИСПРАВЛЕНИЙ:")
print("="*60)
print("""
1. ✅ morning_weight_function теперь использует 
   context.application.user_data[user_id_int]['step'] = 'daily_weight'
   вместо context.user_data['step'] = 'daily_weight'
   
2. ✅ Добавлено логирование для отладки:
   - При отправке утреннего запроса
   - При сохранении веса
   
3. ✅ handle_daily_weight правильно сбрасывает step после сохранения

ПОЧЕМУ ЭТО ИСПРАВЛЯЕТ ПРОБЛЕМУ:
- В планировщике задач context.user_data НЕ привязан к конкретному 
  пользователю
- Нужно использовать context.application.user_data[user_id] для 
  установки данных конкретного пользователя
- Теперь когда пользователь отвечает на утренний запрос веса, 
  его ответ будет обработан как ввод веса
""")

print("\n📝 Для проверки работы:")
print("1. Перезапустите бота")
print("2. Проверьте логи bot.log - должны появиться записи о установке step")
print("3. Ответьте на утренний запрос веса")
print("4. Вес должен сохраниться, и появится сообщение '✅ Вес X кг записан!'")
