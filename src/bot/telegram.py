import os
import logging
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler

from ..sql import crud
from ..sql.database import SessionLocal

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Meta states
STOPPING = map(chr, range(1))

MAIN_SELECTION, REMINDER_SELECTION = map(chr, range(2))

# Stage Definition for Top Level Conversation
SEARCH, REMINDER, REPORT, ABOUT = map(chr, range(4))

# State Definitions for Reminder Level Conversation
LIST_REMINDER, DISABLE_REMINDER, CREATE_REMINDER = map(chr, range(3))

KEYWORD_SEARCH, STOPPING, START_OVER= map(chr, range(3))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update["message"]["chat"]["username"]
    crud.create_user(SessionLocal(), username, chat_id)

    logger.info("User %s started bot", username)

    start_message = """
Welcome to the Flash Sales Bot {}

- To search items on sale enter /search
- To manage your reminders enter /reminder
- To report an issue enter /report
- To learn more about this bot /about
    """.format(username)

    context.bot.send_message(chat_id=chat_id, text=start_message)

    return MAIN_SELECTION

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

    crud.create_reminder(SessionLocal(), user.username, update.message.text)
    update.message.reply_text("Reminder Created")

    return get_create_reminder(update, context)

def list_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is listing all reminders", user.username)
    reminders = crud.get_reminders(SessionLocal(), user.username)
    
    if len(reminders) > 0 :
        text = "Below are the reminders you have set"

        for reminder in reminders:
            text += "\n - {}".format(reminder.keyword)

        update.message.reply_text(text)
        update.message.reply_text("/back to Reminder Menu")
    else:
        update.message.reply_text("You seem not to have any reminders saved, please /reminder and make one")

    return REMINDER

def disable_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s disabling reminder", user.username)
    update.message.reply_text("Please provide the keyword you want to disable for")

    return KEYWORD_SEARCH

def back_to_main(update: Update, context: CallbackContext):
    context.user_data[START_OVER] = True
    start(update, context)

    return END

def back_to_reminder(update: Update, context: CallbackContext):
    context.user_data[START_OVER] = True
    reminder(update, context)

    return END

# def send_reminder(update: Update, context: CallbackContext):
#     user = update.message.from_user
#     logger.info("User %s is listing all reminders", user.username)
#     reminders = crud.get_reminders(SessionLocal(), user.username)
    
#     for reminder in reminders:
#         update.message.reply_text("Reminder on the sales ongoing for '{}'".format(reminder.keyword))

#         items = crud.get_item(SessionLocal(), reminder.keyword)
#         for item in items:
#             update.message.reply_text("""
#                 Name : {} \nOriginal Price : {} \nDiscount Price : {} \nSale Time : {} \nLink : {}
#             """.format(item.item_name, item.item_original_price, item.item_discount_price, item.item_sale_time, item.item_url,))

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

    create_reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('create_reminder', get_create_reminder)],
        states={
            CREATE_REMINDER : [MessageHandler(Filters.text & ~Filters.command, set_create_reminder), ],
        },
        fallbacks=[CommandHandler('back', back_to_reminder)],
        map_to_parent={
            END: REMINDER
        }
    )

    reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('reminder', reminder)],
        states={
            REMINDER : [CommandHandler('list_reminder', list_reminder), CommandHandler('disable_reminder', disable_reminder), create_reminder_conv],
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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_SELECTION: [reminder_conv, search_conv],
            STOPPING: [CommandHandler("start", start)]
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    dispatcher.add_handler(conv_handler)
    
    # Start the Bot
    updater.start_polling()

    updater.idle()