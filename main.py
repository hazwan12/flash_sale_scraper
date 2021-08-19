import sys

from src.bot import telegram
from src.extractor import shopee
from src.sql import models, crud
from src.sql.database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

try:
    args = sys.argv

    if args[1] == "BOT":
        telegram.start_bot()
    
    elif args[1] == "SHOPEE":
        crud.create_items(get_db())

    else:
        print("Invalid Args")

except Exception as e:
    print(e)