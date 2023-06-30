from telebot import TeleBot, ExceptionHandler
from dotenv import dotenv_values

values = dotenv_values()


class ExceptionHandler(ExceptionHandler):
    def handle(self, exception):
        print(str(exception))
        bot.send_message(values['MAINTAINER_CHAT_ID'], f'Ошибка в боте создателей курсов:\n\n{str(exception)}')
        return True


bot = TeleBot(values['BOT_TOKEN_CREATORS'], exception_handler=ExceptionHandler())


# try:
#     conn = psycopg2.connect(dbname=values['NAME_DB'], user=values['USER_DB'], password=values['PASSWORD_DB'], host=values['HOST_DB'])
# except:
#     print('Не получилось подключиться')

# def db_query(query):
#     cur = conn.cursor()
#     cur.execute(query)
#     return cur.fetchall()
