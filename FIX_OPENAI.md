# Исправление ошибки OpenAI API

## Проблема
```
❌ Ошибка анализа фото: You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0
```

## Быстрое решение

### Вариант 1: Автоматическое исправление (рекомендуется)

**На Windows (PowerShell):**
```powershell
./fix_openai.ps1
```

**На Linux/macOS:**
```bash
chmod +x fix_openai.sh
./fix_openai.sh
```

**На любой системе (Python):**
```bash
python fix_openai_auto.py
```

### Вариант 2: Ручное исправление

1. **Проверьте версию OpenAI:**
```bash
pip show openai
```

2. **Если версия < 1.0.0, обновите:**
```bash
pip install openai>=1.0.0
```

3. **Если версия >= 1.0.0, исправьте код:**

Замените в файлах `utils/calorie_calculator.py` и других:

**Было:**
```python
import openai
openai.api_key = OPENAI_API_KEY
response = await openai.ChatCompletion.acreate(...)
```

**Стало:**
```python
from openai import AsyncOpenAI
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
response = await openai_client.chat.completions.create(...)
```

## Проверка исправления

```bash
python test_openai_fix.py
```

## Альтернативное решение (если ничего не помогает)

Откатиться на старую версию OpenAI:
```bash
pip install openai==0.28
```

Но это НЕ рекомендуется, так как старая версия устарела и имеет проблемы с безопасностью.

## После исправления

1. Перезапустите бота
2. Проверьте, что API ключ корректен в `config.py`
3. Убедитесь, что у вас есть доступ к GPT-4 Vision в вашем OpenAI аккаунте

## Поддержка

Если проблема остается, проверьте:
- Правильность API ключа OpenAI
- Наличие средств на счету OpenAI
- Доступность модели `gpt-4-vision-preview`
