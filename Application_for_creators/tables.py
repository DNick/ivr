from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
# from config import db_query
from telegraph import Telegraph
from database.models import *
from telebot.types import *


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Создать свой курс')
btn2 = KeyboardButton('Посмотреть мои курсы')
start_table.add(btn1, btn2)

btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))

topics_table = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton('Все', callback_data='topic_Все'))
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(topics_poll[i]), create_topic_btn(topics_poll[i + 1]))
if len(topics_poll) % 2 == 0:
    topics_table.add(create_topic_btn(topics_poll[-1]))

back_table = ReplyKeyboardMarkup(resize_keyboard=True)
back_table.add(btn_back)

# create_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
# btn1 = KeyboardButton('Отменить последнее действие')
# btn2 = KeyboardButton('Выйти и не сохранить')
# create_course_table.add(btn1, btn2)
# edit_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
# btn1 = KeyboardButton('Изменить общие данные')
# btn2 = KeyboardButton('')


exit_and_not_save_table = ReplyKeyboardMarkup(resize_keyboard=True)
exit_and_not_save_table.add(KeyboardButton('Выйти и не сохранить'))
