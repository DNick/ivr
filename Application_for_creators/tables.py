from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
# from config import db_query
from telegraph import Telegraph
from database.models import *


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


def get_edit_course_table(chat_id):
    auth_url = Users.get(Users.chat_id == chat_id).auth_url
    edit_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton('Изменить общие данные')
    btn2 = KeyboardButton('Добавить тему', web_app=WebAppInfo(auth_url))
    btn3 = KeyboardButton('Поменять темы местами')
    edit_course_table.add(btn1, btn2, btn3)
    return edit_course_table


start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Создать свой курс')
btn2 = KeyboardButton('Посмотреть мои курсы')
start_table.add(btn1, btn2)

btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))

topics_table = InlineKeyboardMarkup(row_width=2)
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


exit_and_not_save_table = ReplyKeyboardMarkup(resize_keyboard=True)
exit_and_not_save_table.add(KeyboardButton('Выйти и не сохранить'))

change_meta_data_table = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton('Название', callback_data='change_title')
btn2 = InlineKeyboardButton('Описание', callback_data='change_description')
btn3 = InlineKeyboardButton('Цена', callback_data='change_price')
btn4 = InlineKeyboardButton('Изображение', callback_data='change_logo')
change_meta_data_table.add(btn1, btn2, btn3, btn4)


yes_no_table = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton('Да', callback_data='yes_choice')
btn2 = InlineKeyboardButton('Нет', callback_data='no_choice')
yes_no_table.add(btn1, btn2)