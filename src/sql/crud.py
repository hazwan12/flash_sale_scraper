from . import models
from ..extractor import Shopee
from .. import utils

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
                    item = existing_item
                    item.item_discount_price = j["discounted_price"]

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
    try:
        user = db.query(models.User).filter(models.User.username == username).first()

        if user:
            user.chat_id = chat_id
        else:
            user = models.User(username=username, chat_id=chat_id)
            db.merge(user)

    except Exception as e:
        print(e)

    finally:
        db.commit()

    db.close()

def create_reminder(db : Session, username : str, keyword : str):
    try:
        status = "Reminder Created"
        reminder = db.query(models.Reminder)\
                    .filter(models.Reminder.active == True)\
                    .filter(models.Reminder.username == username)\
                    .filter(models.Reminder.keyword.contains(keyword))\
                    .first()

        if reminder:
            status = "Reminder for {} already exist, please try another keyword".format(keyword)
        else:
            reminder = models.Reminder(username=username, active=True, keyword=keyword)
            db.add(reminder)

    except Exception as e:
        print(e)

    finally:
        db.commit()

    db.close()

    return status

def get_item(db : Session, search_keyword : str = None):
    try:
        item = db.query(models.Item).filter(models.Item.item_sale_time >= str(datetime.datetime.now().date()))

        if search_keyword:
            item = item.filter(models.Item.item_name.contains(search_keyword))

        item = item.all()
    except Exception as e:
        print(e)

    finally:
        db.close()

    return item

def get_reminders(db : Session, chat_id : str):
    reminder = []
    try:
        user = db.query(models.User).filter(models.User.chat_id == chat_id).first()
        if user:
            reminder = db.query(models.Reminder)\
                        .filter(models.Reminder.active == True)\
                        .filter(models.Reminder.username == user.username)\
                        .all()

    except Exception as e:
        print(e)

    finally:
        db.close()  

    return reminder

def disable_reminder(db : Session, username : str, keyword : str):
    try:
        reminder = db.query(models.Reminder)\
                    .filter(models.Reminder.active == True)\
                    .filter(models.Reminder.username == username)\
                    .filter(models.Reminder.keyword.contains(keyword))\
                    .first()

        if reminder:
            reminder.active = False
            db.merge(reminder)
            status = "Reminder Deactivation Success"

        else :
            status = "Reminder for {} does not exist".format(keyword)
    except Exception as e:
        print(e)

    finally:
        db.commit()

    db.close()

    return status

def get_items_on_sale(db : Session, keyword : str):
    try:
        current_date = utils.get_nearest_hour()
        item = db.query(models.Item)\
                .filter(models.Item.item_sale_time >= str(current_date))\
                .filter(models.Item.item_sale_time <= str(current_date))\
                .filter(models.Item.item_name.contains(keyword))\
                .all()

    except Exception as e:
        print(e)

    finally:
        db.close()

    return item

