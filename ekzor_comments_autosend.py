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

async def handle_discussion_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик сообщений в Discussion Group.
    Отправляет комментарий с картинкой и кнопками под автоматически пересланный пост из канала.
    """
    try:
        message = update.message
        
        # Проверяем, что это автоматическая пересылка из канала
        if not message or not message.forward_from_chat:
            return
        
        # Проверяем, что пересылка из канала (а не из другой группы)
        if message.forward_from_chat.type != 'channel':
            return
        
        # Получаем информацию о канале
        forward_from_chat = message.forward_from_chat
        if forward_from_chat.username:
            channel_username = f"@{forward_from_chat.username}"
        else:
            channel_username = str(forward_from_chat.id)
        
        logger.info(f"Обнаружена пересылка из канала {channel_username} в Discussion Group")
        
        # Проверяем, что это пост из нашего канала
        if CHANNEL_ID.startswith('@'):
            if channel_username != CHANNEL_ID:
                logger.info(f"Пропускаем: канал {channel_username} не совпадает с {CHANNEL_ID}")
                return
        else:
            # Убираем @ если он есть в CHANNEL_ID и сравниваем ID
            expected_id = CHANNEL_ID.replace('@', '').replace('-100', '')
            actual_id = str(forward_from_chat.id).replace('-100', '')
            if expected_id != actual_id:
                logger.info(f"Пропускаем: ID канала {forward_from_chat.id} не совпадает с {CHANNEL_ID}")
                return
        
        logger.info(f"✅ Это наш канал! Отправляем комментарий...")
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("💬 Чат", url=CHAT_URL),
                InlineKeyboardButton("🎵 Яндекс Музыка", url=MUSIC_URL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем комментарий с картинкой в Discussion Group
        if os.path.exists(PHOTO_PATH):
            with open(PHOTO_PATH, 'rb') as photo:
                sent_message = await context.bot.send_photo(
                    chat_id=message.chat.id,  # ID Discussion Group
                    photo=photo,
                    caption=COMMENT_TEXT,
                    reply_markup=reply_markup,
                    reply_to_message_id=message.message_id,  # Отвечаем на пересланный пост
                    parse_mode=ParseMode.HTML
                )
            logger.info(f"✅ Комментарий с картинкой отправлен! Message ID: {sent_message.message_id}")
        else:
            # Если картинка не найдена, отправляем только текст
            sent_message = await context.bot.send_message(
                chat_id=message.chat.id,
                text=COMMENT_TEXT,
                reply_markup=reply_markup,
                reply_to_message_id=message.message_id,
                parse_mode=ParseMode.HTML
            )
            logger.warning(f"⚠️ Картинка не найдена: {PHOTO_PATH}. Отправлен только текст. Message ID: {sent_message.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения: {e}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=context.error)


def main() -> None:
    """Запуск бота"""
    logger.info("=" * 60)
    logger.info("Запуск Ekzor Comments AutoSend Bot...")
    logger.info("=" * 60)
    
    # Проверка конфигурации
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ ОШИБКА: Не указан BOT_TOKEN!")
        logger.error("Установите переменную окружения BOT_TOKEN или отредактируйте файл .env")
        return
    
    logger.info(f"📢 Отслеживаемый канал: {CHANNEL_ID}")
    logger.info(f"🖼️  Путь к картинке: {PHOTO_PATH}")
    logger.info(f"📁 Картинка существует: {os.path.exists(PHOTO_PATH)}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчик ТОЛЬКО для сообщений в группах (Discussion Group)
    # Фильтруем только сообщения с forward_from_chat (автоматические пересылки из канала)
    application.add_handler(
        MessageHandler(
            filters.ChatType.SUPERGROUP & filters.FORWARDED,
            handle_discussion_message
        )
    )
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен и готов к работе!")
    logger.info("🔍 Ожидаю автоматические пересылки постов из канала в Discussion Group...")
    logger.info("=" * 60)
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
