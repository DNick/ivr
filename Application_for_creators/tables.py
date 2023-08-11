from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from utils import set_user_attr
from telegraph import Telegraph
from database.models import *


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


def get_auth_table(auth_url):
    auth_table = InlineKeyboardMarkup()
    btn = InlineKeyboardButton('Нажми на меня', web_app=WebAppInfo(auth_url))
    auth_table.add(btn)
    return auth_table


def get_edit_lesson_table(url):
    add_lesson_table = InlineKeyboardMarkup()
    btn1 = get_edit_btn(url)
    add_lesson_table.add(btn1)
    return add_lesson_table


def get_all_lessons_table(order_of_lessons):
    order_of_lessons = order_of_lessons.split()
    all_lessons_table = InlineKeyboardMarkup()
    telegraph = Telegraph()
    for i in range(len(order_of_lessons)):
        path = Lesson.get_by_id(order_of_lessons[i]).url[len('https://telegra.ph/'):]
        btn = InlineKeyboardButton(telegraph.get_page(path)['title'], callback_data=f'lesson_{i}')
        all_lessons_table.add(btn)

    return all_lessons_table


def get_all_courses_table(courses):
    all_courses_table = InlineKeyboardMarkup()
    for course in courses:
        btn = InlineKeyboardButton(course.title, callback_data=f'course_{course.id}')
        all_courses_table.add(btn)

    return all_courses_table

def get_edit_btn(url):
    return InlineKeyboardButton('Редактировать', web_app=WebAppInfo(url))


btn_back = KeyboardButton('Назад')

edit_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Изменить общие данные')
btn2 = KeyboardButton('Уроки курса')
# btn3 = KeyboardButton('Добавить урок')

edit_course_table.add(btn1, btn2, btn_back)

add_lesson_btn = InlineKeyboardButton('Добавить урок', callback_data='add_lesson')

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Создать свой курс')
btn2 = KeyboardButton('Посмотреть мои курсы')
start_table.add(btn1, btn2)

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
