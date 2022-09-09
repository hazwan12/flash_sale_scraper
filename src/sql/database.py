import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

#SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(DATABASE_URL.replace("postgres", "postgresql"))

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()