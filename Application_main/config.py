from telebot import TeleBot
from dotenv import dotenv_values

values = dotenv_values()

bot = TeleBot(values['BOT_TOKEN_MAIN'])
