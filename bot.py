# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для ConversationHandler
TITLE, DESCRIPTION, CONTACT = range(3)

# ID администратора (твой ID в Telegram)
ADMIN_ID = "ТВОЙ_TELEGRAM_ID"  # Заменить на свой ID

# ID канала (например, @myjobchannel)
CHANNEL_ID = "@myjobchannel"

# Временное хранилище данных пользователя
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я помогу тебе разместить вакансию в канале. Напиши название компании или вакансии:"
    )
    return TITLE

# Получаем название
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['title'] = update.message.text
    await update.message.reply_text("Отлично! Теперь введи описание вакансии:")
    return DESCRIPTION

# Получаем описание
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['description'] = update.message.text
    await update.message.reply_text("Укажи контактную информацию (телефон, email, Telegram):")
    return CONTACT

# Получаем контакт и отправляем админу
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['contact'] = update.message.text

    # Формируем текст для админа
    text_to_admin = (
        f"Новая вакансия для публикации:\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Опубликовать?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем админу
    await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin, reply_markup=reply_markup)

    await update.message.reply_text("Ваша вакансия отправлена на модерацию. После проверки она будет опубликована в канале.")

    return ConversationHandler.END

# Админ нажимает кнопку "Опубликовать"
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Формируем текст для публикации в канал
    post_text = (
        f"💼 ВАКАНСИЯ\n\n"
        f"🔹 {user_data['title']}\n\n"
        f"{user_data['description']}\n\n"
        f"📩 Контакт: {user_data['contact']}"
    )

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
        await query.edit_message_text("✅ Вакансия опубликована в канале.")
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка публикации: {e}")

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Основная функция
def main():
    # Вставь сюда токен своего бота
    TOKEN = "ТОКЕН_БОТА"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(publish, pattern="publish"))

    app.run_polling()

if __name__ == '__main__':
    main()
    # Проверка запуска
print("Бот запущен!")
