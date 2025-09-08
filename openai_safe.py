# -*- coding: utf-8 -*-
"""
Безопасная инициализация OpenAI - блокирует старые методы
"""
import sys
import logging
import traceback
import datetime

# Настраиваем логирование для этого модуля
logger = logging.getLogger(__name__)

def init_safe_openai():
    """Инициализирует безопасную версию OpenAI"""
    try:
        logger.info("🔧 Начинаем инициализацию безопасного OpenAI")
        
        import openai
        logger.info(f"✅ OpenAI модуль импортирован, версия: {openai.__version__ if hasattr(openai, '__version__') else 'неизвестно'}")
        
        # Проверяем что ChatCompletion существует
        if hasattr(openai, 'ChatCompletion'):
            logger.info("📋 openai.ChatCompletion обнаружен, блокируем...")
        else:
            logger.warning("⚠️ openai.ChatCompletion не найден (возможно уже заблокирован)")
        
        # Создаем заблокированный ChatCompletion
        class BlockedChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                error_msg = (
                    "ИСПРАВЛЕНО: openai.ChatCompletion.create больше не поддерживается!\n"
                    "Используйте AsyncOpenAI().chat.completions.create() вместо этого.\n"
                    f"Вызов заблокирован в {datetime.datetime.now()}"
                )
                logger.error(f"🚫 Заблокирован вызов ChatCompletion.create с args={args}, kwargs={kwargs}")
                logger.error(f"📍 Traceback вызова:\n{traceback.format_stack()}")
                raise RuntimeError(error_msg)
            
            @staticmethod
            def acreate(*args, **kwargs):
                error_msg = (
                    "ИСПРАВЛЕНО: openai.ChatCompletion.acreate больше не поддерживается!\n" 
                    "Используйте AsyncOpenAI().chat.completions.create() вместо этого.\n"
                    f"Вызов заблокирован в {datetime.datetime.now()}"
                )
                logger.error(f"🚫 Заблокирован вызов ChatCompletion.acreate с args={args}, kwargs={kwargs}")
                logger.error(f"📍 Traceback вызова:\n{traceback.format_stack()}")
                raise RuntimeError(error_msg)
        
        # Заменяем только ChatCompletion, оставляя остальной модуль нетронутым
        original_chatcompletion = getattr(openai, 'ChatCompletion', None)
        openai.ChatCompletion = BlockedChatCompletion
        
        logger.info("🔧 OpenAI ChatCompletion заблокирован, остальной модуль сохранен")
        
        # Проверяем что блокировка работает
        try:
            openai.ChatCompletion.create()
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Блокировка ChatCompletion.create не работает!")
            return False
        except RuntimeError as e:
            if "ИСПРАВЛЕНО" in str(e):
                logger.info("✅ Блокировка ChatCompletion.create работает корректно")
            else:
                logger.warning(f"⚠️ Блокировка работает, но с неожиданной ошибкой: {e}")
        
        # Сохраняем информацию о блокировке
        openai._safe_blocked = True
        openai._safe_blocked_at = datetime.datetime.now()
        openai._original_chatcompletion = original_chatcompletion
        
        logger.info("🛡️ Безопасная инициализация OpenAI завершена успешно")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ OpenAI library не доступна: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка блокировки OpenAI ChatCompletion: {e}")
        logger.error(f"📍 Полная ошибка: {traceback.format_exc()}")
        return False

def check_openai_safety():
    """Проверяет что OpenAI безопасно инициализирован"""
    try:
        import openai
        
        # Проверяем наличие меток безопасности
        if hasattr(openai, '_safe_blocked') and openai._safe_blocked:
            logger.info(f"✅ OpenAI заблокирован с {openai._safe_blocked_at}")
            return True
        else:
            logger.warning("⚠️ OpenAI не помечен как безопасно заблокированный")
            return False
            
    except ImportError:
        logger.warning("OpenAI library не доступна")
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки безопасности OpenAI: {e}")
        return False

def get_openai_status():
    """Возвращает статус OpenAI модуля"""
    try:
        import openai
        
        status = {
            'imported': True,
            'version': getattr(openai, '__version__', 'неизвестно'),
            'has_chatcompletion': hasattr(openai, 'ChatCompletion'),
            'is_blocked': getattr(openai, '_safe_blocked', False),
            'blocked_at': getattr(openai, '_safe_blocked_at', None)
        }
        
        return status
        
    except ImportError:
        return {'imported': False, 'error': 'OpenAI library не установлена'}
    except Exception as e:
        return {'imported': False, 'error': str(e)}

# Применяем безопасную инициализацию при импорте
logger.info("🚀 Модуль openai_safe загружается...")
init_result = init_safe_openai()

if init_result:
    logger.info("🎉 Модуль openai_safe загружен успешно")
else:
    logger.error("💥 Ошибка загрузки модуля openai_safe")
