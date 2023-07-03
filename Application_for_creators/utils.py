from telebot import types

from config import bot
from database.models import Users


def is_non_negative_digit(text):
    return text.isdigit() and int(text) >= 0


def set_state(chat_id, state):
    query = Users.update({Users.state: state}).where(Users.chat_id == chat_id)
    query.execute()


def get_state(chat_id):
    return Users.get(Users.chat_id == chat_id).state

