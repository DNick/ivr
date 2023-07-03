from datetime import datetime

from telebot.custom_filters import StateFilter
from telebot.types import Message, CallbackQuery
from telebot.handler_backends import State, StatesGroup

from Application_for_creators.utils import is_non_negative_digit
from tables import *
from config import bot
from utils import *


@bot.message_handler(func=lambda msg: msg.text == 'Изменить общие данные')
def handle_change_meta_data_1(msg: Message):
    bot.send_message(msg.chat.id, 'Выберите, что хотите изменить', reply_markup=change_meta_data_table)


@bot.callback_query_handler(func=lambda call: 'change' in call.data)
def handle_change_meta_data_2(call: CallbackQuery):
    course_id = int(get_state(call.message.chat.id).split('_')[1])
    course = Course.get_by_id(course_id)
    if 'title' in call.data:
        bot.send_message(call.message.chat.id, f'Введите новое название (Старое название: `{course.title}`)')
    elif 'description' in call.data:
        bot.send_message(call.message.chat.id, f'Введите новое описание (Старое описание: `{course.description}`)')
    elif 'title' in call.data:
        bot.send_message(call.message.chat.id, f'Введите новую цену (Старая цена: `{course.price}`)')
