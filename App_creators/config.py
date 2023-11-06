import boto3
from telebot import TeleBot, ExceptionHandler
from dotenv import dotenv_values

values = dotenv_values()


class MyExceptionHandler(ExceptionHandler):
    def handle(self, exception):
        print(str(exception))
        bot.send_message(values['MAINTAINER_CHAT_ID'], f'Ошибка в боте создателей курсов:\n\n{str(exception)}')
        return True


bot = TeleBot(values['BOT_TOKEN_CREATORS'], exception_handler=ExceptionHandler())

s3 = boto3.client(
    's3',
    region_name='ru-central1-c',
    aws_access_key_id=values['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=values['AWS_SECRET_ACCESS_KEY'],
    endpoint_url='https://storage.yandexcloud.net'
)
