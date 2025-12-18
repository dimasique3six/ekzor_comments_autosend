#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ekzor Comments AutoSend Bot
Автоматически отправляет комментарий с картинкой и кнопками под каждый пост в канале
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/log/ekzor_comments_autosend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= КОНФИГУРАЦИЯ =============
# Получаем настройки из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel')  # Можно использовать @username или -100xxxxxxxxxx
CHAT_URL = os.getenv('CHAT_URL', 'https://t.me/your_chat')
MUSIC_URL = os.getenv('MUSIC_URL', 'https://music.yandex.ru/users/your_playlist')
PHOTO_PATH = os.getenv('PHOTO_PATH', '/opt/ekzor_comments_autosend/image.jpg')  # Путь к картинке
COMMENT_TEXT = os.getenv('COMMENT_TEXT', '🎵 Слушайте нашу музыку и общайтесь с нами!')

# ============= ОСНОВНАЯ ЛОГИКА =============

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик новых постов в канале.
    Отправляет комментарий с картинкой и кнопками.
    """
    try:
        # Проверяем, что пост из нужного канала
        if update.channel_post.chat.username:
            channel_username = f"@{update.channel_post.chat.username}"
        else:
            channel_username = str(update.channel_post.chat.id)
        
        logger.info(f"Новый пост в канале: {channel_username}")
        
        # Если это не наш канал - игнорируем
        if CHANNEL_ID.startswith('@'):
            if channel_username != CHANNEL_ID:
                return
        else:
            if str(update.channel_post.chat.id) != CHANNEL_ID.replace('@', ''):
                return
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("💬 Чат", url=CHAT_URL),
                InlineKeyboardButton("🎵 Яндекс Музыка", url=MUSIC_URL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем комментарий с картинкой
        if os.path.exists(PHOTO_PATH):
            with open(PHOTO_PATH, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.channel_post.chat.id,
                    photo=photo,
                    caption=COMMENT_TEXT,
                    reply_markup=reply_markup,
                    reply_to_message_id=update.channel_post.message_id,
                    parse_mode=ParseMode.HTML
                )
            logger.info(f"Комментарий с картинкой отправлен к посту {update.channel_post.message_id}")
        else:
            # Если картинка не найдена, отправляем только текст
            await context.bot.send_message(
                chat_id=update.channel_post.chat.id,
                text=COMMENT_TEXT,
                reply_markup=reply_markup,
                reply_to_message_id=update.channel_post.message_id,
                parse_mode=ParseMode.HTML
            )
            logger.warning(f"Картинка не найдена: {PHOTO_PATH}. Отправлен только текст.")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поста: {e}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=context.error)


def main() -> None:
    """Запуск бота"""
    logger.info("Запуск бота...")
    
    # Проверка конфигурации
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("ОШИБКА: Не указан BOT_TOKEN!")
        logger.error("Установите переменную окружения BOT_TOKEN или отредактируйте файл")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчик постов в канале
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен и готов к работе!")
    logger.info(f"Отслеживаемый канал: {CHANNEL_ID}")
    logger.info(f"Путь к картинке: {PHOTO_PATH}")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
