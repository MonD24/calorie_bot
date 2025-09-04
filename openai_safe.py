# -*- coding: utf-8 -*-
"""
Безопасная инициализация OpenAI - блокирует старые методы
"""
import sys
import logging

def init_safe_openai():
    """Инициализирует безопасную версию OpenAI"""
    try:
        import openai
        
        # Создаем заблокированный ChatCompletion
        class BlockedChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                raise RuntimeError(
                    "ИСПРАВЛЕНО: openai.ChatCompletion.create больше не поддерживается!\n"
                    "Используйте AsyncOpenAI().chat.completions.create() вместо этого."
                )
            
            @staticmethod
            def acreate(*args, **kwargs):
                raise RuntimeError(
                    "ИСПРАВЛЕНО: openai.ChatCompletion.acreate больше не поддерживается!\n" 
                    "Используйте AsyncOpenAI().chat.completions.create() вместо этого."
                )
        
        # Заменяем только ChatCompletion, оставляя остальной модуль нетронутым
        openai.ChatCompletion = BlockedChatCompletion
        
        logging.info("🔧 OpenAI ChatCompletion заблокирован, остальной модуль сохранен")
        return True
        
    except ImportError:
        logging.warning("OpenAI library not available")
        return False
    except Exception as e:
        logging.error(f"Ошибка блокировки OpenAI ChatCompletion: {e}")
        return False

# Применяем безопасную инициализацию при импорте
init_safe_openai()
