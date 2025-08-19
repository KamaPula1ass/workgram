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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TITLE, DESCRIPTION, CONTACT, CONFIRM_PAYMENT = range(4)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = "752266705"
CHANNEL_ID = "@workwave_kzn"
PUBLICATION_COST = 30

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Введите название компании или вакансии:"
    )
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание вакансии:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['description'] = update.message.text
    await update.message.reply_text("Укажите контактную информацию (телефон, email, Telegram):")
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['contact'] = update.message.text

    confirmation_text = (
        "📝 Проверьте данные вакансии:\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Подтвердите оплату и отправьте вакансию на модерацию?"
    )

    keyboard = [[InlineKeyboardButton(f"💳 Оплатить {PUBLICATION_COST} ₽", callback_data="pay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
    return CONFIRM_PAYMENT

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    moderation_text = (
        f"📝 НОВАЯ ВАКАНСИЯ (ОПЛАЧЕНО)\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Опубликовать вакансию?"
    )

    keyboard = [[InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_ID, text=moderation_text, reply_markup=reply_markup)

    await query.edit_message_text(
        "✅ Оплата подтверждена!\n"
        "Ваша вакансия отправлена на модерацию.\n"
        "После проверки она будет опубликована в канале @workwave_kzn"
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        f"Стоимость публикации: {PUBLICATION_COST} ₽\n\n"
        "Введите название компании или вакансии:"
    )
    return TITLE

async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    post_text = (
        f"💼 ВАКАНСИЯ\n\n"
        f"🔹 {user_data['title']}\n\n"
        f"{user_data['description']}\n\n"
        f"📩 Контакт: {user_data['contact']}"
    )

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
        await query.edit_message_text("✅ Вакансия успешно опубликована в канале @workwave_kzn!")
        logger.info(f"Вакансия опубликована: {user_data['title']}")
    except Exception as e:
        error_msg = f"❌ Ошибка публикации: {str(e)}"
        await query.edit_message_text(error_msg)
        logger.error(error_msg)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

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
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(check_payment, pattern="check_payment"))
    app.add_handler(CallbackQueryHandler(publish, pattern="publish"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="back_to_start"))

    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
