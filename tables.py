from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton


def create_topic_btn(topic):
    return InlineKeyboardButton(topic, callback_data=f'topic_{topic}')


topics_poll = ['Все', 'Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Программирование',
               'Юриспруденция', 'Психология']

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Найти подходящий курс')
btn2 = KeyboardButton('Создать свой курс')
start_table.add(btn1, btn2)

topics_table = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton('Все', callback_data='topic_Все'))
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(topics_poll[i]), create_topic_btn(topics_poll[i + 1]))
if len(topics_poll) % 2 == 0:
    topics_table.add(create_topic_btn(topics_poll[-1]))
