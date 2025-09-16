# -*- coding: utf-8 -*-
"""
Утилиты для обработки и форматирования ошибок
"""
import logging
import traceback
from typing import Optional


def format_error_message(error: Exception, context: Optional[str] = None, user_data: Optional[str] = None) -> str:
    """
    Форматирует сообщение об ошибке для отправки пользователю

    Args:
        error: Объект исключения
        context: Контекст, где произошла ошибка (например, "при обработке фото")
        user_data: Пользовательские данные для отладки

    Returns:
        Отформатированное сообщение об ошибке
    """
    error_msg = f"❌ Ошибка"

    if context:
        error_msg += f" {context}"

    error_msg += ":\n"
    error_msg += f"`{str(error)}`\n\n"
    error_msg += f"Тип ошибки: {type(error).__name__}\n"

    if user_data:
        error_msg += f"Данные: {user_data}\n"

    error_msg += "\nПопробуйте ещё раз или обратитесь к разработчику."

    return error_msg


def log_detailed_error(error: Exception, context: str, user_id: str = None, extra_data: dict = None):
    """
    Логирует детальную информацию об ошибке

    Args:
        error: Объект исключения
        context: Контекст ошибки
        user_id: ID пользователя (если есть)
        extra_data: Дополнительные данные для логирования
    """
    error_details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'user_id': user_id,
        'traceback': traceback.format_exc()
    }

    if extra_data:
        error_details.update(extra_data)

    logging.error(f"Detailed error report: {error_details}")


async def safe_reply(update_or_query, message: str, **kwargs):
    """
    Безопасная отправка сообщения с обработкой ошибок

    Args:
        update_or_query: Update или CallbackQuery объект
        message: Текст сообщения
        **kwargs: Дополнительные параметры для отправки
    """
    try:
        # Определяем тип объекта и отправляем соответствующим способом
        if hasattr(update_or_query, 'message'):
            # Это Update
            await update_or_query.message.reply_text(message, **kwargs)
        elif hasattr(update_or_query, 'edit_message_text'):
            # Это CallbackQuery
            try:
                await update_or_query.edit_message_text(message, **kwargs)
            except Exception:
                # Если редактирование не удалось, отправляем новое сообщение
                await update_or_query.message.reply_text(message, **kwargs)
    except Exception as e:
        logging.error(f"Failed to send message safely: {e}")
        # В крайнем случае просто логируем
