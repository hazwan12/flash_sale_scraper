from .database import Base

from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    chat_id = Column(String)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String)
    item_original_price = Column(String)
    item_discount_price = Column(String)
    item_url = Column(String)
    item_sale_time = Column(String)

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    active = Column(Boolean)
    keyword = Column(String)