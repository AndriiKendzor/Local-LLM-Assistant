from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'Chats'

    ChatID = Column(Integer, primary_key=True, autoincrement=True)
    Title = Column(String(255), nullable=False)
    Date = Column(DateTime, nullable=False, default=datetime.now)
    KB = Column(Boolean, nullable=False)
    CollectionID = Column(String(255), nullable=False)
    Model = Column(String(255), nullable=False)


class Main(Base):
    __tablename__ = 'Main'

    MessageID = Column(Integer, primary_key=True, autoincrement=True)
    ChatID = Column(Integer, ForeignKey('Chats.ChatID', ondelete='CASCADE'), nullable=False)
    User_m = Column(Text, nullable=False)
    LLm_m = Column(Text, nullable=False)


if __name__ == "__main__":
    engine = create_engine('sqlite:///E:/LocalLLMAssistant/DataBase.db')
    # Створення всіх таблиць
    Base.metadata.create_all(engine)