import sys

from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo

sys.path.append('../../')
from database.models import Topics, Course


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


def get_all_taken_courses_table(courses):
    all_courses_table = InlineKeyboardMarkup()
    for course in courses:
        title = course.title
        btn = InlineKeyboardButton(title, callback_data=f'taken_course_{course.id}')
        all_courses_table.add(btn)

    return all_courses_table


btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))
print(topics_poll)

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Найти подходящий курс', web_app=WebAppInfo('https://dc20-82-204-189-106.ngrok-free.app'))
btn2 = KeyboardButton('Мои курсы')
btn3 = KeyboardButton('Создать курс')
btn4 = KeyboardButton('Оставить отзыв')

start_table.add(btn1, btn2, btn3, btn4)

topics_table = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton('Все', callback_data='topic_Все'))
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(topics_poll[i]), create_topic_btn(topics_poll[i + 1]))
if len(topics_poll) % 2 == 0 and len(topics_poll):
    topics_table.add(create_topic_btn(topics_poll[-1]))

back_table = ReplyKeyboardMarkup(resize_keyboard=True)
back_table.add(btn_back)

create_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Отменить последнее действие')
btn2 = KeyboardButton('Выйти и не сохранить')
create_course_table.add(btn1, btn2)
