'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Dict

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    
class user_refactored(Base):
    __tablename__ = "user_refactored"
    
    user_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_name: Mapped[str] = mapped_column(String)
    
class user_refactored_salted(user_refactored):
    salt: Mapped[str] = mapped_column(String)
    
class friend_request(Base):
    __tablename__ = "friend_request"
    autoInc: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[str] = mapped_column(String)
    receiver: Mapped[str] = mapped_column(String)

class friends_list(Base):
    __tablename__ = "friends"
    autoInc: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_one: Mapped[str] = mapped_column(String)
    user_two: Mapped[str] = mapped_column(String)
    
##############################

class chat_room_obj(Base):
    __tablename__ = "chat_room"
    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_name: Mapped[str] = mapped_column(String)
    
class user_chat_obj(Base):
    __tablename__ = "user_chat"
    user_name: Mapped[str] = mapped_column(String)
    chat_id: Mapped[int] = mapped_column(Integer)
    entry_id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)
    
class message_obj(Base):
    __tablename__ = "message"
    user_name: Mapped[str] = mapped_column(String)
    chat_id: Mapped[int] = mapped_column(Integer)
    time_sent: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    entry_id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)