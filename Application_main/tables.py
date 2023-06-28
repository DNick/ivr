from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton

from database.models import Topics


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


btn_back = KeyboardButton('Назад')

topics_poll = list(map(lambda x: x.text, Topics.select()))
print(topics_poll)

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Найти подходящий курс')
btn2 = KeyboardButton('Создать курс')
btn3 = KeyboardButton('Оставить отзыв')
start_table.add(btn1, btn2, btn3)

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
