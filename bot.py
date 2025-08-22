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

# Состояния для ConversationHandler
START, CHOOSE_METHOD, HELP_TITLE, HELP_DESCRIPTION, HELP_REQUIREMENTS, HELP_SALARY, HELP_CONTACTS, HELP_CONFIRM, READY_VACANCY, CONFIRM_PAYMENT, WAITING_FOR_PAYMENT = range(11)

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

# Цены как в описании канала
PUBLICATION_COST = 150
VIP_COST = 300

# Временное хранилище данных пользователя
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт через кнопку в канале или команду /start"""
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        "Только проверенные компании.\n"
        f"📌 Обычная публикация: {PUBLICATION_COST} ₽\n"
        f"⭐ VIP публикация: {VIP_COST} ₽\n\n"
        "VIP вакансии получают рассылку в 10 активных чатов!\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💼 Добавить вакансию", callback_data="add_vacancy")],
        [InlineKeyboardButton("🔄 Перезапустить бота", callback_data="restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
    return START

# Добавить вакансию
async def add_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление вакансии - выбор метода"""
    query = update.callback_query
    await query.answer()
    
    welcome_text = (
        "💼 Размещение вакансии в канале @workwave_kzn\n\n"
        "Выберите способ размещения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛠️ Помощь в составлении вакансии", callback_data="help_create")],
        [InlineKeyboardButton("📤 Загрузить готовую вакансию", callback_data="ready_vacancy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    return CHOOSE_METHOD

# Обработка выбора метода
async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора метода размещения"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help_create":
        user_data['method'] = "help"
        await query.edit_message_text(
            "📝 Давайте составим вакансию вместе!\n\n"
            "1️⃣ Введите название компании или должности:"
        )
        return HELP_TITLE
    
    elif query.data == "ready_vacancy":
        user_data['method'] = "ready"
        await query.edit_message_text(
            "📤 Отправьте полный текст вакансии:\n\n"
            "Пример:\n"
            "💼 Менеджер по продажам\n\n"
            "🏢 Компания: ООО 'Ромашка'\n"
            "📍 Локация: Казань, офис\n"
            "💰 Зарплата: 50 000 - 80 000 ₽\n"
            "📋 Обязанности: продажа услуг, работа с клиентами\n"
            "🎓 Требования: опыт от 1 года, коммуникабельность\n"
            "📅 График: полный день\n"
            "📞 Контакт: @hr_romashka"
        )
        return READY_VACANCY

# === ПОМОЩЬ В СОСТАВЛЕНИИ ===

# Получаем название
async def help_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия"""
    user_data['title'] = update.message.text
    await update.message.reply_text(
        "2️⃣ Описание компании и вакансии:\n\n"
        "Пример: молодая IT-компания, создающая мобильные приложения. Ищем активного менеджера для развития отдела продаж."
    )
    return HELP_DESCRIPTION

# Получаем описание
async def help_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания"""
    user_data['description'] = update.message.text
    await update.message.reply_text(
        "3️⃣ Требования к кандидату:\n\n"
        "Пример: опыт в продажах от 1 года, знание CRM, коммуникабельность, наличие водительских прав."
    )
    return HELP_REQUIREMENTS

# Получаем требования
async def help_requirements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение требований"""
    user_data['requirements'] = update.message.text
    await update.message.reply_text(
        "4️⃣ Зарплата и условия:\n\n"
        "Пример: 50 000 - 80 000 ₽ + бонусы, график 5/2, офис в центре, ДМС через 3 месяца."
    )
    return HELP_SALARY

# Получаем зарплату
async def help_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение зарплаты"""
    user_data['salary'] = update.message.text
    await update.message.reply_text(
        "5️⃣ Контактная информация:\n\n"
        "Пример: @hr_manager, +7(999)123-45-67, hr@company.ru"
    )
    return HELP_CONTACTS

# Получаем контакты
async def help_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение контактов"""
    user_data['contacts'] = update.message.text
    
    # Формируем предпросмотр вакансии
    preview = (
        f"💼 {user_data['title']}\n\n"
        f"🏢 {user_data['description']}\n\n"
        f"📋 Требования: {user_data['requirements']}\n\n"
        f"💰 {user_data['salary']}\n\n"
        f"📩 {user_data['contacts']}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Всё верно", callback_data="confirm_vacancy")],
        [InlineKeyboardButton("🔄 Перезаполнить", callback_data="restart_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 Проверьте вакансию:\n\n" + preview,
        reply_markup=reply_markup
    )
    return HELP_CONFIRM

# Подтверждение вакансии
async def help_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение вакансии"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_vacancy":
        # Формируем финальный текст вакансии
        user_data['final_text'] = (
            f"💼 {user_data['title']}\n\n"
            f"🏢 {user_data['description']}\n\n"
            f"📋 Требования: {user_data['requirements']}\n\n"
            f"💰 {user_data['salary']}\n\n"
            f"📩 {user_data['contacts']}"
        )
        
        await show_payment_options(query, context)
        return CONFIRM_PAYMENT
    
    elif query.data == "restart_help":
        await query.edit_message_text(
            "📝 Начинаем заново!\n\n"
            "1️⃣ Введите название компании или должности:"
        )
        return HELP_TITLE

# === ГОТОВАЯ ВАКАНСИЯ ===

# Получаем готовую вакансию
async def ready_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение готовой вакансии"""
    user_data['final_text'] = update.message.text
    
    await show_payment_options(update, context, is_callback=False)
    return CONFIRM_PAYMENT

# === ОПЛАТА ===

async def show_payment_options(update_or_query, context, is_callback=True):
    """Показ опций оплаты"""
    payment_text = (
        "💳 Выберите тип публикации:\n\n"
        f"📌 Обычная: {PUBLICATION_COST} ₽\n"
        f"⭐ VIP: {VIP_COST} ₽\n\n"
        "VIP вакансии получают рассылку в 10 активных чатов!"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"📌 Обычная ({PUBLICATION_COST} ₽)", callback_data="regular")],
        [InlineKeyboardButton(f"⭐ VIP ({VIP_COST} ₽)", callback_data="vip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update_or_query.edit_message_text(payment_text, reply_markup=reply_markup)
    else:
        await update_or_query.message.reply_text(payment_text, reply_markup=reply_markup)

# Выбор типа публикации
async def select_publication_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа публикации"""
    query = update.callback_query
    await query.answer()
    
    user_data['publication_type'] = query.data
    cost = VIP_COST if query.data == "vip" else PUBLICATION_COST
    
    payment_text = (
        f"💰 Оплата публикации ({cost} ₽)\n\n"
        "Для оплаты переведите точную сумму на один из реквизитов:\n\n"
        "🔹 СБП по номеру: `+79083420585`\n"
        "🔹 Tinkoff: `5536914122039807`\n\n"
        "❗ Обязательно указывайте комментарий к платежу: `Вакансия`\n"
        "После оплаты нажмите кнопку \"Проверить оплату\""
    )

    keyboard = [
        [InlineKeyboardButton("✅ Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(payment_text, reply_markup=reply_markup)
    return WAITING_FOR_PAYMENT

# Проверка оплаты
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
        f"🔹 Вакансия:\n{user_data['final_text']}\n\n"
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

# Возврат к оплате
async def back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору оплаты"""
    query = update.callback_query
    await query.answer()
    await show_payment_options(query, context)
    return CONFIRM_PAYMENT

# Публикация вакансии админом
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Публикация вакансии в канале"""
    query = update.callback_query
    await query.answer()

    try:
        # Публикуем в канал
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID, 
            text=user_data['final_text']
        )
        
        # Добавляем кнопку "Разместить свою вакансию"
        keyboard = [[InlineKeyboardButton(
            "💼 Разместить свою вакансию", 
            url=f"https://t.me/workgramm_bot?start=publish"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_reply_markup(
            chat_id=CHANNEL_ID,
            message_id=message.message_id,
            reply_markup=reply_markup
        )
        
        # Если VIP - уведомление о рассылке
        if user_data.get('publication_type') == "vip":
            await query.edit_message_text(
                "✅ Вакансия успешно опубликована в канале @workwave_kzn!\n"
                "📩 VIP рассылка будет отправлена в 10 активных чатов!"
            )
        else:
            await query.edit_message_text("✅ Вакансия успешно опубликована в канале @workwave_kzn!")
        
        logger.info("Вакансия опубликована")
    except Exception as e:
        error_msg = f"❌ Ошибка публикации: {str(e)}"
        await query.edit_message_text(error_msg)
        logger.error(error_msg)

# Перезапустить бота
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапустить бота"""
    query = update.callback_query
    await query.answer()
    
    # Возвращаемся к началу
    await start(query, context)
    return START

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена размещения"""
    await update.message.reply_text("Операция отменена. Чтобы начать заново, введите /start")
    return ConversationHandler.END

# Основная функция запуска
def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()

    # Настройка диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                CallbackQueryHandler(add_vacancy, pattern="add_vacancy"),
                CallbackQueryHandler(restart, pattern="restart")
            ],
            CHOOSE_METHOD: [CallbackQueryHandler(choose_method, pattern="^(help_create|ready_vacancy)$")],
            
            # Помощь в составлении
            HELP_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, help_title)],
            HELP_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, help_description)],
            HELP_REQUIREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, help_requirements)],
            HELP_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, help_salary)],
            HELP_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, help_contacts)],
            HELP_CONFIRM: [CallbackQueryHandler(help_confirm, pattern="^(confirm_vacancy|restart_help)$")],
            
            # Готовая вакансия
            READY_VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ready_vacancy)],
            
            # Оплата
            CONFIRM_PAYMENT: [CallbackQueryHandler(select_publication_type, pattern="^(regular|vip)$")],
            WAITING_FOR_PAYMENT: [
                CallbackQueryHandler(check_payment, pattern="check_payment"),
                CallbackQueryHandler(back_to_payment, pattern="back_to_payment")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавляем обработчики
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(publish, pattern="publish"))

    # Запуск бота
    logger.info("Бот готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
