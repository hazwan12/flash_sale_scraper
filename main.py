import sys

from src.bot import telegram
from src.extractor import shopee
from src.sql import models, crud
from src.sql.database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

try:
    args = sys.argv

    if args[1].upper() == "BOT":

        if args[2].upper() == "TELEGRAM":
            telegram.start_bot()

        else:
            print("Invalid BOT Args")
    
    elif args[1].upper() == "SCRAPE":

        if args[2].upper() == "SHOPEE":
            crud.create_items(SessionLocal())

        else:
            print("Invalid EXTRACT Args")
    else:
        print("Invalid Args")

except Exception as e:
    print(e)