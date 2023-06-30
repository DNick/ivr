from datetime import datetime

from telebot.types import Message

from tables import *
from config import *


@bot.message_handler(commands=['start'])
def handle_start(msg):
    print(msg.chat.id)
    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)


@bot.message_handler(func=lambda msg: msg.text == 'Найти подходящий курс')
def handle_find(msg: Message):
    bot.send_message(msg.chat.id, 'Вот список тем, выберите одну из них', reply_markup=topics_table)
    bot.send_message(msg.chat.id, 'или выйдите назад', reply_markup=back_table)


@bot.message_handler(func=lambda msg: msg.text == 'Создать курс')
def handle_create(msg: Message):
    bot.send_message(msg.chat.id, 'Перейдите по ссылке в меню создания курса: https://t.me/Teach_and_learn_creators_bot')


@bot.message_handler(func=lambda msg: msg.text == 'Оставить отзыв')
def handle_give_feedback(msg: Message):
    bot.send_message(msg.chat.id, 'Напишите Ваш отзыв в одном сообщении и я обязательно передам его разработчикам')
    bot.register_next_step_handler(msg, enter_feedback)


def enter_feedback(msg):
    bot.send_message(values['MAINTAINER_CHAT_ID'], 'Поступил новый отзыв:\n\n' + msg.text)
    bot.send_message(msg.chat.id, 'Спасибо! Вы помогаете делать наш сервис лучше')



@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg):
    bot.send_message(msg.chat.id, 'Я тебя не понимаю, лучше нажми на одну из кнопочек снизу')

# @bot.callback_query_handler(func=lambda call: 'back' in call.data)
# def answer(call):
#     if call.data == 'back_start_menu':
#         bot.send_message(call.message.chat.id, 'Вы в главном меню', reply_markup=start_table)


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.infinity_polling()
