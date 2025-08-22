# bot.py
import os
import logging
import asyncio
import aiohttp
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

# Состояния для ConversationHandler
TITLE, DESCRIPTION, CONTACT, CONFIRM_PAYMENT = range(4)

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")

# Проверка наличия токена
if not TOKEN:
    logger.error("ТОКЕН НЕ НАЙДЕН! Установите переменную окружения TOKEN")
    exit(1)

# ID администратора (ваш Telegram ID)
ADMIN_ID = "752266705"

# Имя вашего Telegram-канала
CHANNEL_ID = "@workwave_kzn"

# Стоимость публикации вакансии (в рублях)
PUBLICATION_COST = 300
VIP_COST = 800

# Временное хранилище данных пользователя
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и начало размещения вакансии"""
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        "Только проверенные компании.\n"
        f"Обычная публикация: {PUBLICATION_COST} ₽\n"
        f"VIP публикация: {VIP_COST} ₽\n\n"
        "Выберите тип публикации:"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"📌 Обычная ({PUBLICATION_COST} ₽)", callback_data="regular")],
        [InlineKeyboardButton(f"⭐ VIP ({VIP_COST} ₽)", callback_data="vip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return TITLE

# Выбор типа публикации
async def select_publication_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа публикации"""
    query = update.callback_query
    await query.answer()
    
    user_data['publication_type'] = query.data
    cost = VIP_COST if query.data == "vip" else PUBLICATION_COST
    
    await query.edit_message_text(
        f"Вы выбрали {'VIP' if query.data == 'vip' else 'обычную'} публикацию.\n"
        f"Стоимость: {cost} ₽\n\n"
        "Введите название компании или вакансии:"
    )
    return TITLE

# Получаем название
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия вакансии"""
    user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание вакансии:")
    return DESCRIPTION

# Получаем описание
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания вакансии"""
    user_data['description'] = update.message.text
    await update.message.reply_text("Укажите контактную информацию (телефон, email, Telegram):")
    return CONTACT

# Получаем контакт и подтверждаем оплату
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение контактной информации и подтверждение оплаты"""
    user_data['contact'] = update.message.text
    
    pub_type = "VIP" if user_data.get('publication_type') == "vip" else "Обычная"
    cost = VIP_COST if user_data.get('publication_type') == "vip" else PUBLICATION_COST
    
    confirmation_text = (
        f"📝 Проверьте данные вакансии:\n\n"
        f"Тип публикации: {pub_type}\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Стоимость: {cost} ₽\n\n"
        "Подтвердите оплату для размещения вакансии?"
    )

    keyboard = [[InlineKeyboardButton(f"💳 Оплатить {cost} ₽", callback_data="pay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
    return CONFIRM_PAYMENT

# Обработка кнопки оплаты
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки оплаты"""
    query = update.callback_query
    await query.answer()
    
    cost = VIP_COST if user_data.get('publication_type') == "vip" else PUBLICATION_COST
    
    payment_text = (
        f"💰 Оплата публикации ({cost} ₽)\n\n"
        "Для оплаты переведите точную сумму на один из реквизитов:\n\n"
        "🔹 СБП по номеру: `+79872500303`\n"
        "🔹 Tinkoff: `5536914009734478`\n"
        "🔹 Qiwi: `https://qiwi.com/n/PROWEB777`\n\n"
        "❗ Обязательно указывайте комментарий к платежу: `Вакансия`\n"
        "После оплаты нажмите кнопку \"Проверить оплату\""
    )

    keyboard = [
        [InlineKeyboardButton("✅ Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(payment_text, reply_markup=reply_markup)

# Проверка оплаты (временно автоматически одобряем)
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка оплаты и отправка на модерацию"""
    query = update.callback_query
    await query.answer()
    
    pub_type = "VIP" if user_data.get('publication_type') == "vip" else "Обычная"
    cost = VIP_COST if user_data.get('publication_type') == "vip" else PUBLICATION_COST

    # Отправляем вакансию админу на модерацию
    moderation_text = (
        f"📝 НОВАЯ ВАКАНСИЯ (ОПЛАЧЕНО)\n"
        f"Тип: {pub_type} ({cost} ₽)\n\n"
        f"🔹 Название: {user_data['title']}\n"
        f"🔹 Описание: {user_data['description']}\n"
        f"🔹 Контакт: {user_data['contact']}\n\n"
        f"Опубликовать вакансию?"
    )

    keyboard = [[InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]]
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
    """Возврат к началу размещения"""
    query = update.callback_query
    await query.answer()
    
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        "Только проверенные компании.\n"
        f"Обычная публикация: {PUBLICATION_COST} ₽\n"
        f"VIP публикация: {VIP_COST} ₽\n\n"
        "Выберите тип публикации:"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"📌 Обычная ({PUBLICATION_COST} ₽)", callback_data="regular")],
        [InlineKeyboardButton(f"⭐ VIP ({VIP_COST} ₽)", callback_data="vip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    return TITLE

# Публикация вакансии админом
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Публикация вакансии в канале"""
    query = update.callback_query
    await query.answer()

    # Формируем текст для публикации
    pub_type = "⭐ VIP ВАКАНСИЯ" if user_data.get('publication_type') == "vip" else "💼 ВАКАНСИЯ"
    
    post_text = (
        f"{pub_type}\n\n"
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

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена размещения"""
    await update.message.reply_text("Операция отменена. Чтобы начать заново, введите /start")
    return ConversationHandler.END

# Функция для "пробуждения" бота
async def ping_self():
    """Функция для "пробуждения" бота каждые 10 минут"""
    # Замените YOUR_RENDER_APP_URL на ваш URL из Render
    url = "https://workgram-kz.onrender.com"  # <-- ВАЖНО: Заменить на ваш URL!
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logger.info(f"Ping: {resp.status}")
        except Exception as e:
            logger.error(f"Ping error: {e}")
        await asyncio.sleep(600)  # 10 минут

def start_ping_loop():
    """Запуск фоновой задачи для пинга"""
    loop = asyncio.get_event_loop()
    loop.create_task(ping_self())

# Основная функция запуска
def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Запуск пинга
    start_ping_loop()
    
    # Настройка диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TITLE: [
                CallbackQueryHandler(select_publication_type, pattern="^(regular|vip)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)
            ],
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
