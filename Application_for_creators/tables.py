from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
# from config import db_query
from telegraph import Telegraph
from database.models import *
from telebot.types import *


telegraph = Telegraph()
resp = telegraph.create_account(short_name='Teach&Learn')


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))
print(topics_poll)
# a = WebAppInfo('https://edit.telegra.ph/auth/PdqYiMy9kdy7em1HMEAeRa2HWc9KMAABL0z3L8b5jH')
# 'https://edit.telegra.ph/auth/DaVkLpttVef0gjKeKGyqrCpiGRSxT2cwb7PUuinnuA'
# print()
start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Создать свой курс', web_app=WebAppInfo(resp['auth_url']))
btn2 = KeyboardButton('Посмотреть мои курсы')
start_table.add(btn1, btn2)

topics_table = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton('Все', callback_data='topic_Все'))
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(topics_poll[i]), create_topic_btn(topics_poll[i + 1]))
if len(topics_poll) % 2 == 0:
    topics_table.add(create_topic_btn(topics_poll[-1]))

back_table = ReplyKeyboardMarkup(resize_keyboard=True)
back_table.add(btn_back)

create_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Отменить последнее действие')
btn2 = KeyboardButton('Выйти и не сохранить')
create_course_table.add(btn1, btn2)
