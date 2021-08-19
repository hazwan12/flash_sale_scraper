from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

from ..sql.database import SessionLocal

BOT_TOKEN = '1999877100:AAHj7H5m2feACSe6gJ4KxTF00ytw8wOfrtY'

updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def start(update, context):
    chat_id = update.effective_chat.id
    username = update["message"]["chat"]["username"]

    start_message = """
    Welcome to the Flash Sales Bot {}

     - To search items on sale enter /search
     - To list all your reminders enter /list_reminders
     - To report an issue enter /report
    """.format(username)

    context.bot.send_message(chat_id=chat_id, text=start_message)

def search():
    pass

def remind():
    pass

def start_bot():
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()