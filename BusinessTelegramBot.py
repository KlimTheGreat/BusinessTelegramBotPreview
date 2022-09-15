"""Basic example for a bot that can receive payment from user."""
# библиотека - https://github.com/python-telegram-bot/python-telegram-bot
# Ю касса - https://yookassa.ru/docs/support/payments/onboarding/integration/cms-module/telegram
# mySql - https://dev.mysql.com/doc/connector-python/en/connector-python-examples.html
import html
import json
import logging
import traceback
import MySqlConnector as db
from os import environ
from time import strftime
from telegram import (
    LabeledPrice,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    PreCheckoutQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.DEBUG,  # info
    datefmt=strftime("%d-%m-%y %H:%M:%S")
)
logger = logging.getLogger(__name__)

# get secret constants from os environment variables
TELEGRAM_BOT_TOKEN = environ["TELEGRAM_BOT_TOKEN"]
PAYMENT_PROVIDER_TOKEN = environ["PAYMENT_PROVIDER_TOKEN"]

# other constants
DEVELOPER_CHAT_ID = 368475952
CURRENCY_RUB = "RUB"

(
    NAME,
    PHONE,
    CONFIRM_PHONE,
    EMAIL,
    CONFIRM_EMAIL
) = range(5)


def is_integer(n) -> bool:
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


# displays info, saves new user data
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    if user.id in await db.get_all_user_ids():
        user_name = await db.get_user_name(user.id)
        await update.message.reply_text(
            f"Привет, *{user_name}*!\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
        return await data_handler(update, context)
    else:
        user_name = user.first_name
        await db.save_main_user_data(
            user.id,
            user_name,
            user.is_bot
        )
        reply_keyboard = [['Да', 'Нет']]
        await update.message.reply_text(
            "Привет, давай познакомимся! Я бизнес-бот для твоего бизнеса.\n"
            f"Могу ли я называть тебя *{user_name}*?\n"
            "Отправь мне *Да* или *Нет*.\n\n"
            "_закончить разговор - /cancel_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,
                input_field_placeholder=f"Ты {user_name}?"
            )
        )
        return NAME


async def data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_name = await db.get_user_name(user_id)
    user_phone = await db.get_user_phone(user_id)
    user_email = await db.get_user_email(user_id)
    await update.message.reply_text(
        "Твои данные: \n\n"
        f"Имя: *{user_name}*\n"
        f"Телефон: *{user_phone}*\n"
        f"Email: *{user_email}*\n\n",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    await help_handler(update, context)
    return ConversationHandler.END


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Команды:*\n"
        "/help - посмотреть команды бота\n"
        "/pay <сумма> - тестовый запрос на оплату\n"
        "/data - посмотреть свои данные\n"
        "/delete - удалить все свои данные\n\n"
        "*Разработчик* - @KlimTheGreat\n"
        "_Спасибо, что заглянули!\n"
        "Этого бота я сделал бесплатно, специально для демонстрации, но следующего уже надеюсь сделать для вас :)\n"
        "У меня есть опыт создания ботов на хакатонах с получением наград и я знаю много функций телеги.\n"
        "В коммерческий проект я готов вложить много сил и, при необходимости, реализовать сложный алгоритм.\n"
        "Пишите, если нужен бот)\n"
        "С ув. Клим @KlimTheGreat_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    await db.save_temp_name(update.message.from_user.id, user_name)
    reply_keyboard = [['Да', 'Нет']]
    await update.message.reply_text(
        f"Я могу называть тебя *{user_name}*?\n"
        "Отправь мне *Да* или *Нет*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder=f"Ты {user_name}?"
        ),
    )
    return NAME


async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Окей, тогда напиши мне свое имя.",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def name_ok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await db.set_temp_name(update.message.from_user.id)
    button = KeyboardButton(text="Отправить свой контакт", request_contact=True)
    reply_keyboard = [[button]]
    await update.message.reply_text(
        "Класс! Теперь можешь отправить мне свой номер?\n"
        "Нажми на кнопку или напиши телефон вручную.\n\n"
        "_пропустить - /skip_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Ваш номер телефона"
        ),
    )
    return PHONE


async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_message.contact:
        user_contact = update.effective_message.contact
        user_phone = user_contact.phone_number
    else:
        user_phone = update.message.text
    reply_keyboard = [['Сохранить', 'Изменить']]
    await db.save_temp_phone(update.message.from_user.id, user_phone)
    await update.message.reply_text(
        f"Отлично, твой номер {user_phone}?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Ваш номер телефона"
        ),
    )
    return CONFIRM_PHONE


async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button = KeyboardButton(text="Отправить свой контакт", request_contact=True)
    reply_keyboard = [[button]]
    await update.message.reply_text(
        "Окей, отправь телефон заново, либо нажми на кнопку.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Ваш номер телефона"
        ),
    )
    return PHONE


async def wrong_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button = KeyboardButton(text="Отправить свой контакт", request_contact=True)
    reply_keyboard = [[button]]
    await update.message.reply_text(
        "Неверный телефон.\n"
        "Пожалуйста, попробуйте еще раз.\n\n"
        "_тех. поддержка - @klimthegreat_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Ваш номер телефона"
        ),
    )
    return PHONE


async def confirm_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await db.set_temp_phone(update.message.from_user.id)
    await update.message.reply_text(
        "Супер!\n"
        "А теперь отправь, пожалуйста, свой email.\n\n"
        "_пропустить - /skip_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return EMAIL


async def skip_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Хорошо, а теперь напиши, пожалуйста, свой email.\n\n"
        "_пропустить - /skip_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return EMAIL


async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_email = update.message.text
    reply_keyboard = [['Сохранить', 'Изменить']]
    await db.save_temp_email(update.message.from_user.id, user_email)
    await update.message.reply_text(
        f"Отлично, твой email - {user_email}\n"
        "Сохранить?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Ваш email"
        ),
    )
    return CONFIRM_EMAIL


async def change_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Окей, отправь email заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return EMAIL


async def wrong_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Неверный email.\n"
        "Пожалуйста, попробуйте еще раз.\n\n"
        "_тех. поддержка - @klimthegreat_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return EMAIL


async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    await db.set_temp_email(user_id)
    await update.message.reply_text(
        "Супер, спасибо!",
        reply_markup=ReplyKeyboardRemove()
    )
    return await data_handler(update, context)


async def skip_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Хорошо, спасибо!",
        reply_markup=ReplyKeyboardRemove()
    )
    await data_handler(update, context)
    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Беседа окончена, команды:\n"
        "_запрос на оплату - /pay <сумма>_\n",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await db.remove_user_data(update.message.from_user.id)
    await update.message.reply_text(
        "Все Ваши данные были удалены из базы.\n"
        "_/start - начать беседу заново_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )


# sends an invoice without shipping-payment
async def invoice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (len(context.args) > 0) and is_integer(context.args[0]) and (0 < int(context.args[0]) < 1001):
        price = int(context.args[0])
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title="Товар №1",
            description="Тестовый товар вашего бизнеса",
            photo_url="https://i.imgur.com/x4CDdRD.jpeg",
            payload="Custom-Payload",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=CURRENCY_RUB,
            prices=[LabeledPrice("Товар №1", price * 100)],
            max_tip_amount=5000*100,
            suggested_tip_amounts=[100*100, 200*100, 300*100],
            # получить имейл, если необходим
            # need_email=True,
            # send_email_to_provider=True,
            # получить телефон, если необходим
            # need_phone_number=True,
            # send_phone_number_to_provider=True,
            # если имейл или телефон уже есть, нужно передать его через provider_data[receipt[]]
            # внутри receipt save_payment_method=True если нужно сохранить метод оплаты для последующих авто платежей
            # для повторения платежа добавляем поле payment_method_id в receipt
            # provider_data={
            #     "save_payment_method": True
            # }
        )
        await update.message.reply_text(
            "Чтобы провести тестовую оплату, введите реквизиты тестовой карты:\n"
            "`1111 1111 1111 1026`\n"
            "`12/22`\n"
            "`000`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "Неверная сумма.\n"
            "Минимум 1, максимум 1000.\n\n"
            "_Пример: /pay 500_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )


# answers the PreCheckoutQuery
async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != "Custom-Payload":
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        await query.answer(ok=True)


# confirms successful payment
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    await db.save_user_paid(message.from_user.id, True)
    logger.info(f"New payment: {message.from_user.id} -> {message.successful_payment.provider_payment_charge_id}")
    await update.message.reply_text(
        "Спасибо за оплату! (тестовую)\n"
        "Теперь в базе данных указано, что вы оплатили услугу\n\n"
        "*Разработчик* - @KlimTheGreat\n"
        "_Пишите, если нужен бот)_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )


# run the bot
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(7).get_updates_read_timeout(42).build()

    # check mysql
    db.check_mysql()

    # regex for validating messages
    phone_regex = r"^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$"
    email_regex = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?" \
                  r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

    # add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        states={
            NAME: [
                CommandHandler("cancel", cancel_handler),
                MessageHandler(filters.Regex("^(Да|да)$"), name_ok),
                MessageHandler(filters.Regex("^(Нет|нет)$"), change_name),
                MessageHandler(filters.TEXT, name_handler),
            ],
            PHONE: [
                CommandHandler("skip", skip_phone),
                CommandHandler("cancel", cancel_handler),
                MessageHandler(filters.CONTACT, phone_handler),
                MessageHandler(filters.Regex(phone_regex), phone_handler),
                MessageHandler(filters.TEXT, wrong_phone),
            ],
            CONFIRM_PHONE: [
                CommandHandler("cancel", cancel_handler),
                MessageHandler(filters.Regex("^(Сохранить|сохранить)$"), confirm_phone),
                MessageHandler(filters.Regex("^(Изменить|изменить)$"), change_phone),
            ],
            EMAIL: [
                CommandHandler("skip", skip_email),
                CommandHandler("cancel", cancel_handler),
                MessageHandler(filters.Regex(email_regex), email_handler),
                MessageHandler(filters.TEXT, wrong_email),
            ],
            CONFIRM_EMAIL: [
                CommandHandler("cancel", cancel_handler),
                MessageHandler(filters.Regex("^(Сохранить|сохранить)$"), confirm_email),
                MessageHandler(filters.Regex("^(Изменить|изменить)$"), change_email),
            ],
        },
    )
    application.add_handler(conv_handler)

    # data
    application.add_handler(CommandHandler("data", data_handler))  # show
    application.add_handler(CommandHandler("delete", delete_handler))  # delete

    # invoice
    application.add_handler(CommandHandler("pay", invoice_callback))  # send
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))  # pre-checkout handler to final check
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)  # successful payment handler
    )

    # help
    application.add_handler(CommandHandler("help", help_handler))  # on command
    application.add_handler(MessageHandler(filters.TEXT, help_handler))  # on unknown text

    # error handler
    application.add_error_handler(error_handler)

    # run the bot
    application.run_polling()


if __name__ == "__main__":
    main()
