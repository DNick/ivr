from datetime import datetime

from Application_for_creators.utils import *
from tables import *
from config import bot
from PIL import Image
from handlers.create_course import *


@bot.message_handler(commands=['start'])
def handle_start(msg):
    is_registered = Users.select().where(Users.chat_id == msg.chat.id)
    if not is_registered:
        telegraph = Telegraph()
        response = telegraph.create_account(short_name='Teach&Learn course')
        # Сделать может быть ввод номера карты пользователя
        Users.create(chat_id=msg.chat.id, access_courses_token=response['access_token'], auth_url=response['auth_url'])

    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)


@bot.message_handler(func=lambda msg: msg.text == 'Посмотреть мои курсы')
def handle_show_my_courses(msg: Message):
    bot.set_state(msg.from_user.id, 'back_main')


@bot.message_handler(content_types=['text', 'photo', 'video', 'file'])
def handle_strange_msg(msg: Message):
    bot.send_message(msg.chat.id, 'Я Вас не понимаю, лучше нажми на одну из кнопочек снизу')


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.add_custom_filter(StateFilter())
    bot.infinity_polling()
