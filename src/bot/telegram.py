import os
import datetime
import logging
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler, PicklePersistence

from .. import utils

from ..sql import crud
from ..sql.database import SessionLocal

# Enable logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger("src.bot.telegram")

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAIN_SELECTION, REMINDER_SELECTION = map(chr, range(2))

# Stage Definition for Top Level Conversation
SEARCH, REMINDER, BUGREPORT, ABOUT, SUPPORT = map(chr, range(5))

# State Definitions for Reminder Level Conversation
LIST_REMINDER, DISABLE_REMINDER, CREATE_REMINDER = map(chr, range(3))

KEYWORD_SEARCH, STOPPING, START_OVER= map(chr, range(3))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

def sale_reminder(context: CallbackContext):
    logger.info("Searching reminders for chat_id %s", context.job.context)
    reminders = crud.get_reminders(SessionLocal(), context.job.context)
    
    sale_items = []
    
    if len(reminders) > 0:
        
        for reminder in reminders:
            for item in crud.get_items_on_sale(SessionLocal(), reminder.keyword):

                text = """
Name : {} \nOriginal Price : {} \nDiscount Price : {} \nSale Time : {} \nLink : {}
                """.format(item.item_name, item.item_original_price, item.item_discount_price, item.item_sale_time, item.item_url)

                sale_items.append(text)

    if len(sale_items) > 0:
        context.bot.send_message(chat_id=context.job.context, text="Reminder on Items on Sale")
        for text in sale_items:
            context.bot.send_message(chat_id=context.job.context, text=text)

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update["message"]["chat"]["username"]
    crud.create_user(SessionLocal(), username, chat_id)

    logger.info("User %s started bot", username)

    start_message = """
Welcome to the Flash Sales Bot {}

- To search items on sale: /search
- To manage your reminders: /reminder
- To make a bug report: /bug_report
- To support the developer /support
    """.format(username)

    context.bot.send_message(chat_id=chat_id, text=start_message)

    active_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not active_jobs:
        #for job in active_jobs:
        #    job.schedule_removal()
        context.job_queue.run_repeating(callback=sale_reminder, interval=3600, name=str(chat_id), context=chat_id, first=utils.get_nearest_hour_add_10mins())

    return MAIN_SELECTION

def dummy_convo(update: Update, context: CallbackContext):
    pass

def support(update: Update, context: CallbackContext):
    username = update["message"]["chat"]["username"]
    logger.info("User %s initiated support conversation", username)

    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("paynow.jpg", "rb"))
    context.bot.send_message(chat_id=update.effective_chat.id, text="""
Like the app? Show your appreciation by donating to my PayNow.
Any amount helps as this will be primarily used to pay the cost hosting this.
/back to Main Menu
""")

    return CommandHandler('back', back_to_main)

def bug_report(update : Update, context: CallbackContext):
    username = update["message"]["chat"]["username"]
    logger.info("User %s initiated bug report conversation", username)

    context.bot.send_message(chat_id=update.effective_chat.id, text="""
Please fill in the bug report form here : https://forms.gle/UAhJQpxKbmXwKULH8
/back to main menu
""")

    return BUGREPORT

def get_search_keyword(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s initiated search by keyword", user.username)
    update.message.reply_text("Please provide a keyword of the item you want to search else /back to main menu")

    return SEARCH

def set_search_keyword(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is searching for %s", user.username, update.message.text)

    if len(update.message.text) <= 2:
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
    logger.info("User %s initiated reminder conversation", user.username)
    
    update.message.reply_text("""
- To list all your reminders /list_reminder
- To disable a reminder /disable_reminder
- To create a new rminder /create_reminder
- Back to main menu /back
    """)

    return REMINDER

def get_create_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is creating a reminder", user.username)
    update.message.reply_text("""
Please provide the keyword you want to set a reminder for 
Else /back to main menu
    """)

    return CREATE_REMINDER

def set_create_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is creating reminder for keyword %s", user.username, update.message.text)

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
    logger.info("User %s is disabling a reminder", user.username)

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
    logger.info("User %s is disabling reminder for keyword %s", user.username, update.message.text)

    status = crud.disable_reminder(SessionLocal(), user.username, update.message.text)
    update.message.reply_text(status)

    return get_disable_reminder(update, context)

def back_to_main(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is navigating back to main conversation", user.username)
    context.user_data[START_OVER] = True
    start(update, context)

    return END

def back_to_reminder(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is navigating back to reminder conversation", user.username)
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
    persistence = PicklePersistence(filename='flash_sale_concierge')
    updater = Updater(token=BOT_TOKEN, persistence=persistence)

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
        },
        name="disable_reminder_conv",
        persistent=True,
    )

    create_reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('create_reminder', get_create_reminder)],
        states={
            CREATE_REMINDER : [MessageHandler(Filters.text & ~Filters.command, set_create_reminder),],
        },
        fallbacks=[CommandHandler('back', back_to_reminder)],
        map_to_parent={
            END: REMINDER
        },
        name="create_reminder_conv",
        persistent=True,
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
        },
        name="list_reminder_conv",
        persistent=True,
    )

    reminder_conv = ConversationHandler(
        entry_points=[CommandHandler('reminder', reminder)],
        states={
            REMINDER : [list_reminder_conv, disable_reminder_conv, create_reminder_conv],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        },
        name="reminder_conv",
        persistent=True,
    )

    search_conv = ConversationHandler(
        entry_points=[CommandHandler('search', get_search_keyword)],
        states={
            SEARCH : [MessageHandler(Filters.text & ~Filters.command, set_search_keyword)],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        },
        name="search_conv",
        persistent=True,
    )

    support_conv = ConversationHandler(
        entry_points=[CommandHandler('support', support)],
        states={
            SUPPORT : [MessageHandler(Filters.text & ~Filters.command, dummy_convo)],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        },
        name="support_conv",
        persistent=True,
    )

    bugreport_conv = ConversationHandler(
        entry_points=[CommandHandler('bug_report', bug_report)],
        states={
            BUGREPORT : [MessageHandler(Filters.text & ~Filters.command, dummy_convo)],
        },
        fallbacks=[CommandHandler('back', back_to_main)],
        map_to_parent={
            END: MAIN_SELECTION
        },
        name="bugreprot_conv",
        persistent=True,
    )


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_SELECTION: [reminder_conv, search_conv, support_conv, bugreport_conv],
            STOPPING: [CommandHandler("start", start)]
        },
        fallbacks=[CommandHandler("stop", stop),],
        name="main_conv",
        persistent=True,
    )

    dispatcher.add_handler(conv_handler)
    
    # Add job queues to existing users once bot restarts
    users = crud.get_users(SessionLocal())
    for user in users:
        logger.info("Reinstating Job Queue for User : {}".format(user.username))
        updater.job_queue.run_repeating(
            callback=sale_reminder, interval=3600, 
            name=str(user.chat_id), context=user.chat_id, 
            first=utils.get_nearest_hour_add_10mins()
        )
    
    # Start the Bot
    updater.start_polling()

    updater.idle()