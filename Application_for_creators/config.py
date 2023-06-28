from telebot import TeleBot
from dotenv import dotenv_values

values = dotenv_values()

bot = TeleBot(values['BOT_TOKEN_CREATORS'])

# try:
#     conn = psycopg2.connect(dbname=values['NAME_DB'], user=values['USER_DB'], password=values['PASSWORD_DB'], host=values['HOST_DB'])
# except:
#     print('Не получилось подключиться')

# def db_query(query):
#     cur = conn.cursor()
#     cur.execute(query)
#     return cur.fetchall()
