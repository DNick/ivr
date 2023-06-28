from datetime import datetime

from telebot.types import Message

from tables import *
from config import bot


@bot.message_handler(commands=['start'])
def handle_start(msg):
    print(telegraph.get_page_list())
    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)


@bot.message_handler(func=lambda msg: msg.text == 'Создать свой курс')
def handle_create_course(msg: Message):
    bot.set_state(msg.from_user.id, 'back_main')
    bot.send_message(msg.chat.id, 'Введите название курса', reply_markup=create_course_table)


# @bot.message_handler(func=lambda msg: 'Назад' in msg.text or 'Выйти и не сохранить' in msg.text)
# def answer(msg):
#     if bot.get_state(msg.from_user.id) == 'back_main':
#         bot.send_message(msg.chat.id, 'Вы в главном меню', reply_markup=start_table)


@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg):
    bot.send_message(msg.chat.id, 'Я тебя не понимаю, лучше нажми на одну из кнопочек снизу')


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.infinity_polling()
