from telebot import TeleBot
import psycopg2
# from dotenv import dotenv_values
import os
# values = dotenv_values(".env")
try:
    conn = psycopg2.connect(dbname=os.getenv('NAME_DB'), user=os.getenv('USER_DB'), password=os.getenv('PASSWORD_DB'), host=os.getenv('HOST_DB'))
except:
    print('Не получилось подключиться')

bot = TeleBot(os.getenv('BOT_TOKEN'))
