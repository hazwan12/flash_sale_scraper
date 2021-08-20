import os
import logging
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

from ..sql import crud
from ..sql.database import SessionLocal

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

KEYWORD = range(1)

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update["message"]["chat"]["username"]

    logger.info("User %s started bot", username)

    start_message = """
    Welcome to the Flash Sales Bot {}

     - To search items on sale enter /search
     - To list all your reminders enter /list_reminders
     - To report an issue enter /report
     - To stop this chat /cancel
    """.format(username)

    context.bot.send_message(chat_id=chat_id, text=start_message)

def search(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s initiated search", user.username)
    update.message.reply_text("Please provide a keyword of the item you want to search")

    return KEYWORD

def keyword(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s is searching for %s", user.username, update.message.text)
    items = crud.get_item(SessionLocal(), update.message.text)

    update.message.reply_text("The following items match the keyword you are looking for:")

    for item in items:
        update.message.reply_text("""
            Item Name : {}
            Item Original Price : {}
            Item Discount Price : {}
            Item Sale Time : {}
            Item Link : {}
        """.format(item.item_name, item.item_original_price, item.item_discount_price, item.item_sale_time, item.item_url,))

def remind(update: Update, context: CallbackContext):
    pass

def cancel(update: Update, context: CallbackContext) -> int:
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

    # Add the start handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Add conversation handler
    convo_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search)],
        states={
            KEYWORD: [MessageHandler(Filters.text, keyword)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(convo_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()