from telebot import types

from config import bot


def is_non_negative_digit(text):
    return text.isdigit() and int(text) >= 0
