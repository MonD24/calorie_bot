#!/bin/bash
# Bash скрипт для исправления OpenAI API на Linux/macOS

echo "🔧 Исправление OpenAI API..."

# Найти все Python файлы
python_files=$(find . -name "*.py" ! -name "fix_openai_auto.py")
file_count=$(echo "$python_files" | wc -l)

echo "📄 Найдено Python файлов: $file_count"

fixed_count=0

for file in $python_files; do
    if [[ -f "$file" ]]; then
        # Создаем резервную копию
        cp "$file" "$file.bak"
        
        # Применяем исправления
        sed -i.tmp \
            -e 's/import openai$/from openai import AsyncOpenAI/' \
            -e 's/import openai$/from openai import AsyncOpenAI/' \
            -e 's/openai\.api_key\s*=\s*\(.*\)/openai_client = AsyncOpenAI(api_key=\1)/' \
            -e 's/openai\.ChatCompletion\.create(/openai_client.chat.completions.create(/' \
            -e 's/openai\.ChatCompletion\.acreate(/openai_client.chat.completions.create(/' \
            -e 's/await openai\.ChatCompletion\.acreate(/await openai_client.chat.completions.create(/' \
            "$file"
        
        # Проверяем, были ли изменения
        if ! cmp -s "$file" "$file.bak"; then
            echo "✅ Исправлен: $(basename "$file")"
            ((fixed_count++))
        fi
        
        # Удаляем временные файлы
        rm -f "$file.tmp" "$file.bak"
    fi
done

echo ""
echo "🎯 Результат:"
echo "   Обработано файлов: $file_count"
echo "   Исправлено файлов: $fixed_count"

if [[ $fixed_count -gt 0 ]]; then
    echo ""
    echo "⚠️  Рекомендации после исправления:"
    echo "1. Перезапустите бота"
    echo "2. Убедитесь, что установлена актуальная версия OpenAI:"
    echo "   pip install openai>=1.0.0"
    echo "3. Проверьте, что API ключ корректен"
else
    echo ""
    echo "✅ Все файлы уже используют новый OpenAI API"
fi

echo ""
echo "Для проверки запустите: python test_openai_fix.py"