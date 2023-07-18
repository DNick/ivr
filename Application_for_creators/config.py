import boto3
from telebot import TeleBot, ExceptionHandler
from dotenv import dotenv_values

values = dotenv_values()


# class ExceptionHandler(ExceptionHandler):
#     def handle(self, exception):
#         print(str(exception))
#         bot.send_message(values['MAINTAINER_CHAT_ID'], f'Ошибка в боте создателей курсов:\n\n{str(exception)}')
#         return True
# , exception_handler=ExceptionHandler()

bot = TeleBot(values['BOT_TOKEN_CREATORS'])

s3 = boto3.client(
    's3',
    region_name='ru-central1-c',
    aws_access_key_id=values['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=values['AWS_SECRET_ACCESS_KEY'],
    endpoint_url='https://storage.yandexcloud.net'
)

# try:
#     conn = psycopg2.connect(dbname=values['NAME_DB'], user=values['USER_DB'], password=values['PASSWORD_DB'], host=values['HOST_DB'])
# except:
#     print('Не получилось подключиться')

# def db_query(query):
#     cur = conn.cursor()
#     cur.execute(query)
#     return cur.fetchall()
