import sys

from src.bot import telegram
from src.extractor import shopee
from src.sql import models, crud
from src.sql.database import engine, SessionLocal

import logging
logger = logging.getLogger("main")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

try:
    args = sys.argv
    logger.info("Received Args {}".format(", ".join(args)))

    if args[1].upper() == "BOT":
        

        if args[2].upper() == "TELEGRAM":
            logger.info("Starting Telegram Bot")
            telegram.start_bot()

        else:
            logger.error("Invalid 2nd BOT Args")
    
    elif args[1].upper() == "SCRAPE":

        if args[2].upper() == "SHOPEE":
            logger.info("Starting Shopee Scrape")
            crud.create_items(SessionLocal())

        else:
            logger.error("Invalid 2nd SCRAPE Args")
    else:
        logger.error("Invalid 1st Args")

except Exception as e:
    logger.error(e)