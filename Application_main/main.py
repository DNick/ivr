from datetime import datetime

from telebot import types
from telebot.types import Message

from tables import *
from config import bot


@bot.message_handler(commands=['start'])
def handle_start(msg):
    print(msg)
    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)

@bot.message_handler(func=lambda msg: msg.text == 'Найти подходящий курс')
def handle_find(msg: Message):
    bot.set_state(msg.from_user.id, 'back_main')
    bot.send_message(msg.chat.id, 'Вот список тем, выберите одну из них', reply_markup=topics_table)
    bot.send_message(msg.chat.id, 'или выйдите назад', reply_markup=back_table)


@bot.message_handler(func=lambda msg: 'Назад' in msg.text or 'Выйти и не сохранить' in msg.text)
def answer(msg):
    if bot.get_state(msg.from_user.id) == 'back_main':
        bot.send_message(msg.chat.id, 'Вы в главном меню', reply_markup=start_table)


# @bot.callback_query_handler(func=lambda call: 'back' in call.data)
# def answer(call):
#     if call.data == 'back_start_menu':
#         bot.send_message(call.message.chat.id, 'Вы в главном меню', reply_markup=start_table)


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.infinity_polling()
