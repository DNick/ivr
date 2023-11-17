import sys

from dotenv import dotenv_values
from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from database.models import Topics


values = dotenv_values()


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


def get_all_taken_courses_table(courses, is_rate=False, is_feedback=False):
    """
    :param courses: Курсы
    :param is_rate: Для оценивания или нет
    :param is_feedback: Для обратной связи или нет
    :return: Клавиатуру с проходимыми пользователем курсами (с параметрами)
    """
    all_courses_table = InlineKeyboardMarkup()
    for course in courses:
        title = course.title
        if is_rate:
            callback = f'rate_course_{course.id}'
        elif is_feedback:
            callback = f'give_feedback_creator_{course.id}'
        else:
            callback = f'taken_course_{course.id}'
        btn = InlineKeyboardButton(title, callback_data=callback)
        all_courses_table.add(btn)

    return all_courses_table


def get_pay_course_table(payment_url, price, label):
    """
    :param payment_url: Ссылка на оплату
    :param price: Цена
    :param label: Метка транзакции для отслеживания
    :return: Клавиатура для оплаты курса
    """
    pay_course_table = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton(f'Оплатить {price} RUB', url=payment_url)
    btn2 = InlineKeyboardButton('Я оплатил!', callback_data=f'pay_course_{label}')
    pay_course_table.add(btn1, btn2)
    return pay_course_table


btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Найти подходящий курс', web_app=WebAppInfo(values['INDEX_PAGE_URL']))
btn2 = KeyboardButton('Мои курсы')
btn3 = KeyboardButton('Создать курс')
btn4 = KeyboardButton('Оценить курс')
btn5 = KeyboardButton('Оставить отзыв')

start_table.add(btn1, btn2, btn3, btn4, btn5)


rate_course_table = InlineKeyboardMarkup()
sp_of_btns = []
for i in range(1, 11):
    btn = InlineKeyboardButton(str(i), callback_data=f'get_rate_mark_{i}')
    sp_of_btns.append(btn)

rate_course_table.row(*sp_of_btns[:5])
rate_course_table.row(*sp_of_btns[5:])

feedback_for_table = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton('Разработчикам', callback_data='feedback_for_developers')
btn2 = InlineKeyboardButton('Создателю какого-то курса', callback_data='feedback_for_creator')
feedback_for_table.row(btn1, btn2)


topics_table = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton('Все', callback_data='topic_Все'))
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(topics_poll[i]), create_topic_btn(topics_poll[i + 1]))
if len(topics_poll) % 2 == 0 and len(topics_poll):
    topics_table.add(create_topic_btn(topics_poll[-1]))

back_table = ReplyKeyboardMarkup(resize_keyboard=True)
back_table.add(btn_back)
