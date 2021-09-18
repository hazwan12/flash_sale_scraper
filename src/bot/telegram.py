import os
import datetime
import logging
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler

from .. import utils

from ..sql import crud
from ..sql.database import SessionLocal

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAIN_SELECTION, REMINDER_SELECTION = map(chr, range(2))

# Stage Definition for Top Level Conversation
SEARCH, REMINDER, REPORT, ABOUT, SUPPORT = map(chr, range(5))

# State Definitions for Reminder Level Conversation
LIST_REMINDER, DISABLE_REMINDER, CREATE_REMINDER = map(chr, range(3))

KEYWORD_SEARCH, STOPPING, START_OVER= map(chr, range(3))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

def sale_reminder(context: CallbackContext):
    logger.info("Searching reminders for chat_id %s", context.job.context)
    reminders = crud.get_reminders(SessionLocal(), context.job.context)

    if len(reminders) > 0:
        context.bot.send_message(chat_id=context.job.context, text="Reminder on Items on Sale")
        for reminder in reminders:
            for item in crud.get_items_on_sale(SessionLocal(), reminder.keyword):
                text = """
Name : {} \nOriginal Price : {} \nDiscount Price : {} \nSale Time : {} \nLink : {}
                """.format(item.item_name, item.item_original_price, item.item_discount_price, item.item_sale_time, item.item_url)
                
                current_time = utils.get_datetime_tz()
                sale_time = utils.get_datetime_from_str(item.item_sale_time)
                
                if sale_time > current_time and current_time < sale_time + datetime.timedelta(hours=1):
                    context.bot.send_message(chat_id=context.job.context, text=text)

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update["message"]["chat"]["username"]
    crud.create_user(SessionLocal(), username, chat_id)

    logger.info("User %s started bot", username)

    start_message = """
Welcome to the Flash Sales Bot {}

- To search items on sale enter /search
- To manage your reminders enter /reminder
- To support the developer /support
    """.format(username)

    context.bot.send_message(chat_id=chat_id, text=start_message)

    active_jobs = context.job_queue.get_jobs_by_name(chat_id)
    
    if not active_jobs:
        context.job_queue.run_repeating(callback=sale_reminder, interval=3600, name=str(chat_id), context=chat_id, first=utils.get_nearest_hour_add_10mins())

    return MAIN_SELECTION

def dummy_convo(update: Update, context: CallbackContext):
    pass

def support(update: Update, context: CallbackContext):
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("paynow.jpg", "rb"))
    context.bot.send_message(chat_id=update.effective_chat.id, text="""
Like the app? Show your appreciation by donating to my PayNow.
Any amount helps as this will be primarily used to pay the cost hosting this.
/back to Main Menu
""")

    return CommandHandler('back', back_to_main)

def get_search_keyword(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s initiated search", user.username)
    update.message.reply_text("Please provide a keyword of the item you want to search else /back to main menu")

    return SEARCH

def set_search_keyword(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is searching for %s", user.username, update.message.text)

    if len(update.message.text) <= 3:
        update.message.reply_text("Please provide a keyword longer then 3 characters")

    else:
        items = crud.get_item(SessionLocal(), update.message.text)

        if len(items) > 0:
            update.message.reply_text("""
                The following items match the keyword you are looking for:
            """)

            for item in items:
                update.message.reply_text("""
                    Name : {} \nOriginal Price : {} \nDiscount Price : {} \nSale Time : {} \nLink : {}
                """.format(item.item_name, item.item_original_price, item.item_discount_price, item.item_sale_time, item.item_url,))

        else:
            update.message.reply_text("""
                We can't find anything with the provided keyword, please try a new one
            """)

    return get_search_keyword(update, context)

def reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s initiated reminder", user.username)
    
    update.message.reply_text("""
- To list all your reminders /list_reminder
- To disable a reminder /disable_reminder
- To create a new rminder /create_reminder
- Back to main menu /back
    """)

    return REMINDER

def get_create_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s creating reminder", user.username)
    update.message.reply_text("""
Please provide the keyword you want to set a reminder for 
Else /back to main menu
    """)

    return CREATE_REMINDER

def set_create_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is creating reminder for %s", user.username, update.message.text)

    status = crud.create_reminder(SessionLocal(), user.username, update.message.text)
    update.message.reply_text(status)

    return get_create_reminder(update, context)

def list_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is listing all reminders", user.username)
    reminders = crud.get_reminders(SessionLocal(), update.effective_chat.id)
    
    if len(reminders) > 0 :
        text = "Below are the active reminders for your account"

        for reminder in reminders:
            text += "\n - {}".format(reminder.keyword)

        update.message.reply_text(text)
        update.message.reply_text("""
Please choose an option below
    - /disable_reminder to remove an existing reminder
    - /create_reminder to create a reminder
    - /back to reminder menu
        """)
    else:
        update.message.reply_text("""
There are no reminders currently for your account
    - /create_reminder to create a reminder
    - /back to return to the reminder menu
        """)

    return REMINDER

def get_disable_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s disabling reminder", user.username)

    text = "No Reminders Set"
    reminders = crud.get_reminders(SessionLocal(), update.effective_chat.id)
    if len(reminders) > 0:
        text = "".join(["\n - {}".format(reminder.keyword) for reminder in reminders])

    update.message.reply_text("""
Please provide the keyword you want to disable reminder for.
Below are your active reminders: {}
Else /back to the reminder menu
    """.format(text))

    return DISABLE_REMINDER

def set_disable_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is disabling reminder for %s", user.username, update.message.text)

    status = crud.disable_reminder(SessionLocal(), user.username, update.message.text)
    update.message.reply_text(status)

    return get_disable_reminder(update, context)

def back_to_main(update: Update, context: CallbackContext):
    context.user_data[START_OVER] = True
    start(update, context)

    return END

def back_to_reminder(update: Update, context: CallbackContext):
    context.user_data[START_OVER] = True
    reminder(update, context)

    return END

def stop(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def start_bot():
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    disable_reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('disable_reminder', get_disable_reminder)],
        states={
            DISABLE_REMINDER : [MessageHandler(Filters.text & ~Filters.command, set_disable_reminder),],
        },
        fallbacks=[CommandHandler('back', back_to_reminder)],
        map_to_parent={
            END: REMINDER
        }
    )

    create_reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('create_reminder', get_create_reminder)],
        states={
            CREATE_REMINDER : [MessageHandler(Filters.text & ~Filters.command, set_create_reminder),],
        },
        fallbacks=[CommandHandler('back', back_to_reminder)],
        map_to_parent={
            END: REMINDER
        }
    )

    list_reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('list_reminder', list_reminder)],
        states={
            CREATE_REMINDER : [CommandHandler('create_reminder', get_create_reminder)],
            DISABLE_REMINDER : [CommandHandler('disable_reminder', get_disable_reminder)]
        },
        fallbacks=[CommandHandler('back', back_to_reminder)],
        map_to_parent={
            END: REMINDER
        }
    )

    reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('reminder', reminder)],
        states={
            REMINDER : [list_reminder_conv, disable_reminder_conv, create_reminder_conv],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        }
    )

    search_conv = ConversationHandler(
        entry_points=[CommandHandler('search', get_search_keyword)],
        states={
            SEARCH : [MessageHandler(Filters.text & ~Filters.command, set_search_keyword)],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        }
    )

    support_conv = ConversationHandler(
        entry_points=[CommandHandler('support', support)],
        states={
            SUPPORT : [MessageHandler(Filters.text & ~Filters.command, dummy_convo)],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        }
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_SELECTION: [reminder_conv, search_conv, support_conv],
            STOPPING: [CommandHandler("start", start)]
        },
        fallbacks=[CommandHandler("stop", stop),]
    )

    dispatcher.add_handler(conv_handler)
    
    # Start the Bot
    updater.start_polling()

    updater.idle()