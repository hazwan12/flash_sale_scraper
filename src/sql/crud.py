from . import models
from ..extractor import Shopee

import datetime
from sqlalchemy.orm import Session

def create_items(db : Session):
    x = Shopee().extract()
    x = x["content"]

    for i in x:
        for j in i["sale_items"]:
            try:
                # Search if Items already exist for the sale time
                existing_item = db.query(models.Item)\
                                .filter(models.Item.item_name == j["name"])\
                                .filter(models.Item.item_sale_time == i["sale_time"])\
                                .first()

                # If exist update the discount price
                if existing_item:
                    item = models.Item(
                        item_name = existing_item.item_name, 
                        item_original_price = existing_item.item_original_price, 
                        item_discount_price = j["discounted_price"], 
                        item_url = existing_item.item_url, 
                        item_sale_time = existing_item.item_sale_time
                    )
                
                else:
                    item = models.Item(
                        item_name = j["name"],
                        item_original_price = j["original_price"],
                        item_discount_price = j["discounted_price"], 
                        item_url = j["url"],
                        item_sale_time = i["sale_time"],
                    )

                db.merge(item)

            except Exception as e:
                print(e)

            finally:
                db.commit()

    db.close()

def create_user(db : Session, username : str, chat_id : int):
    user = db.query(models.User).filter(models.User.username == username).all()

    if len(user) > 0:
        db_user = models.User(username=username, chat_id=chat_id)
        db.merge(db_user)
        db.commit()

def create_reminder(db : Session, username : str, keyword : str):
    db_reminder = models.Reminder(username=username, active=True, keyword=keyword)
    db.merge(db_reminder)
    db.commit()

def get_item(db : Session, search_keyword : str = None):
    item = db.query(models.Item).filter(models.Item.item_sale_time >= str(datetime.datetime.now()))

    if search_keyword:
        item = item.filter(models.Item.item_name.contains(search_keyword))

    return item.all()

def get_reminders(db : Session, username : str):
    return db.query(models.Reminder)\
            .filter(models.Reminder.active == True)\
            .filter(models.Reminder.username == username)\
            .all()

