# bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для анкеты
TITLE, DESCRIPTION, CONTACT, CONFIRM_PAYMENT = range(4)

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")

# Проверка токена
if not TOKEN:
    logger.error("ТОКЕН НЕ НАЙДЕН! Установите переменную окружения TOKEN")
    exit(1)

# Замените на свой Telegram ID (узнать через @userinfobot)
ADMIN_ID = "752266705"

# Замените на имя вашего канала
CHANNEL_ID = "@workwave_kzn"

# Стоимость публикации в рублях
PUBLICATION_COST = 30

# Хранилище данных пользователя
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Введите название компании или вакансии:"
    )
    await update.message.reply_text(welcome_text)
    return TITLE

# Получаем название
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание вакансии:")
    return DESCRIPTION

# Получаем описание
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['description'] = update.message.text
    await update.message.reply_text("Укажите контактную информацию (телефон, email, Telegram):")
    return CONTACT

# Получаем контакт
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['contact'] = update.message.text

    # Формируем текст для подтверждения
    confirmation_text = (
        "📝 Проверьте данные вакансии:\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Подтвердите оплату и отправьте вакансию на модерацию?"
    )

    keyboard = [
        [InlineKeyboardButton(f"💳 Оплатить {PUBLICATION_COST} ₽", callback_data="pay")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
    return CONFIRM_PAYMENT

# Обработка кнопки оплаты
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Здесь будет инструкция по оплате
    payment_text = (
        f"💰 Оплата публикации ({PUBLICATION_COST} ₽)\n\n"
        "Для оплаты переведите ровно 30 рублей на карту или кошелек:\n"
        "🔹 Qiwi: `+79991234567`\n"
        "🔹 Карта: `1234 5678 9012 3456`\n\n"
        "❗ После оплаты нажмите кнопку \"Проверить оплату\""
    )

    keyboard = [
        [InlineKeyboardButton("✅ Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(payment_text, reply_markup=reply_markup)

# Проверка оплаты (временно автоматически одобряем)
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Отправляем вакансию админу на модерацию
    moderation_text = (
        f"📝 НОВАЯ ВАКАНСИЯ (ОПЛАЧЕНО)\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Опубликовать вакансию?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID, 
        text=moderation_text, 
        reply_markup=reply_markup
    )

    await query.edit_message_text(
        "✅ Оплата подтверждена!\n"
        "Ваша вакансия отправлена на модерацию.\n"
        "После проверки она будет опубликована в канале @workwave_kzn"
    )

# Возврат к началу
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Введите название компании или вакансии:"
    )
    await query.edit_message_text(welcome_text)
    return TITLE

# Публикация вакансии админом
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Формируем текст для публикации
    post_text = (
        f"💼 ВАКАНСИЯ\n\n"
        f"🔹 {user_data['title']}\n\n"
        f"{user_data['description']}\n\n"
        f"📩 Контакт: {user_data['contact']}"
    )

    try:
        # Публикуем в канал
        await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
        await query.edit_message_text("✅ Вакансия успешно опубликована в канале @workwave_kzn!")
        logger.info(f"Вакансия опубликована: {user_data['title']}")
    except Exception as e:
        error_msg = f"❌ Ошибка публикации: {str(e)}"
        await query.edit_message_text(error_msg)
        logger.error(error_msg)

# Отмена (если добавишь команду /cancel)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Основная функция запуска
def main():
    logger.info("Запуск бота...")
    
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()

    # Настройка диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            CONFIRM_PAYMENT: [
                CallbackQueryHandler(pay, pattern="pay"),
                CallbackQueryHandler(back_to_start, pattern="back_to_start")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавляем обработчики
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(check_payment, pattern="check_payment"))
    app.add_handler(CallbackQueryHandler(publish, pattern="publish"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="back_to_start"))

    # Запуск бота
    logger.info("Бот готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
