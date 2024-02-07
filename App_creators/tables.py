from telebot.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import App_creators.utils as utils
from telegraph import Telegraph

from App_creators.config import bot
from database.models import *

btn_back = KeyboardButton('Назад')


def create_topic_btn(topic, id):
    return InlineKeyboardButton(topic, callback_data=f'topic_{id}')


def get_auth_table(auth_url):
    """
    :param auth_url: Ссылка для авторизации
    :return Клавиатура с кнопкой авторизации
    """
    auth_table = InlineKeyboardMarkup()
    btn = InlineKeyboardButton('Нажми на меня', web_app=WebAppInfo(auth_url))
    auth_table.add(btn)
    return auth_table


def get_edit_lesson_table(url):
    """
    :param url: Ссылка на страницу определённого урока
    :return: Клавиатура с кнокой редактирования урока
    """
    add_lesson_table = InlineKeyboardMarkup()
    btn1 = get_edit_btn(url)
    add_lesson_table.add(btn1)
    return add_lesson_table


def get_all_lessons_table(order_of_lessons, for_creator=True):
    """
    :param order_of_lessons: Id нужных уроков в правильном порядке через пробел
    :param for_creator: Если False, то кнопки при нажатии ведут сразу на страницу урока.
    Иначе после нажатия, открывается меню для редактирования этого урока
    :return: Клавиатура со всеми уроками
    """
    order_of_lessons = order_of_lessons.split()
    all_lessons_table = InlineKeyboardMarkup()
    telegraph = Telegraph()
    for i in range(len(order_of_lessons)):
        domain = 'https://telegra.ph/'
        path = Lesson.get_by_id(order_of_lessons[i]).url[len(domain):]
        if for_creator:
            btn = InlineKeyboardButton(telegraph.get_page(path)['title'], callback_data=f'lesson_{i}')
        else:
            btn = InlineKeyboardButton(telegraph.get_page(path)['title'], web_app=WebAppInfo(domain + path))

        all_lessons_table.add(btn)

    return all_lessons_table


def get_all_courses_table(courses, for_creator=True):
    """
    :param courses: Курсы, проходимые пользователем или созданные пользователем
    :param for_creator: В зависимости от этого параметра (для создателя или нет)
    в кнопки записывается разные callback_data, что помогает предоставлять их разное поведение
    :return: Клавиатура со всеми курсами
    """
    all_courses_table = InlineKeyboardMarkup()
    for course in courses:
        if for_creator:
            callback = f'course_{course.id}'
        else:
            callback = f'taken_course_{course.id}'
        btn = InlineKeyboardButton(course.title, callback_data=f'course_{course.id}')
        all_courses_table.add(btn)

    return all_courses_table


def get_edit_btn(url):
    return InlineKeyboardButton('Редактировать', web_app=WebAppInfo(url))


def get_moving_lesson_table(chat_id, order_of_lessons, lesson_index, delta):
    """
    :param chat_id: Chat_id пользователя
    :param order_of_lessons: Id нужных уроков в правильном порядке через пробел
    :param lesson_index: Индекс урока из клавиатуры
    :param delta: Если 1, то урок перемещают к концу, если -1 - к началу
    :return: Клавиатура для перемещения определённого урока
    """
    jsn = InlineKeyboardMarkup().de_json(utils.get_user_attr(chat_id, 'all_lessons_table')).to_dict()
    lesson_index += delta
    jsn['inline_keyboard'][lesson_index - delta][0], jsn['inline_keyboard'][lesson_index][0] = \
        jsn['inline_keyboard'][lesson_index][0], jsn['inline_keyboard'][lesson_index - delta][0]
    moving_lesson_table = InlineKeyboardMarkup().de_json(jsn)
    utils.set_user_attr(chat_id, 'all_lessons_table', jsn)

    up_btn = InlineKeyboardButton('⬆', callback_data='swap_up')
    save_order_btn = InlineKeyboardButton('Сохранить', callback_data='save_order')
    down_btn = InlineKeyboardButton('⬇', callback_data=f'swap_down')
    if len(order_of_lessons.split()) == 1:
        moving_lesson_table.row(empty_btn, save_order_btn, empty_btn)
    elif lesson_index == 0:
        moving_lesson_table.row(empty_btn, save_order_btn, down_btn)
    elif lesson_index == len(order_of_lessons.split()) - 1:
        moving_lesson_table.row(up_btn, save_order_btn, empty_btn)
    else:
        moving_lesson_table.row(up_btn, save_order_btn, down_btn)

    return moving_lesson_table


def get_edit_course_table(chat_id):
    """
    :param chat_id: Chat_id пользователя
    :return: Клавиатуру редактирования курса
    """
    course_id = utils.get_user_attr(chat_id, 'current_course')
    edit_course_table = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton('Изменить общие данные')
    btn2 = KeyboardButton('Уроки курса')
    btn3 = KeyboardButton('Назад')
    btn4 = KeyboardButton('Удалить курс')
    edit_course_table.add(btn1, btn2, btn3, btn4)
    course = Course.get_by_id(course_id)
    if not course.publication_date:
        btn5 = KeyboardButton('Опубликовать курс в интернет')
        edit_course_table.add(btn5)
    return edit_course_table


add_lesson_btn = InlineKeyboardButton('Добавить урок', callback_data='add_lesson')

start_table = ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = KeyboardButton('Создать свой курс')
btn2 = KeyboardButton('Посмотреть мои курсы')
start_table.add(btn1, btn2)

topics_poll = list(map(lambda x: [x.text, x.id], Topics.select()))

topics_table = InlineKeyboardMarkup(row_width=2)
for i in range(1, len(topics_poll[1:]), 2):
    topics_table.row(create_topic_btn(*topics_poll[i]), create_topic_btn(*topics_poll[i + 1]))
if len(topics_poll) % 2 == 0:
    topics_table.add(create_topic_btn(*topics_poll[-1]))

back_table = ReplyKeyboardMarkup(resize_keyboard=True)
back_table.add(btn_back)

exit_and_not_save_table = ReplyKeyboardMarkup(resize_keyboard=True)
exit_and_not_save_table.add(KeyboardButton('Выйти и не сохранить'))

change_meta_data_table = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton('Название', callback_data='change_title')
btn2 = InlineKeyboardButton('Описание', callback_data='change_description')
btn3 = InlineKeyboardButton('Цена', callback_data='change_price')
btn4 = InlineKeyboardButton('Изображение', callback_data='change_logo')
btn5 = InlineKeyboardButton('Cфера', callback_data='change_topic')
change_meta_data_table.add(btn1, btn2, btn3, btn4, btn5)

yes_no_table = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton('Да', callback_data='yes_choice')
btn2 = InlineKeyboardButton('Нет', callback_data='no_choice')
yes_no_table.add(btn1, btn2)

empty_btn = InlineKeyboardButton(text=' ', callback_data=' ')


def update_access_tokens():
    """
    Функция для обновления telegra.ph токенов. Использовать в крайнем случае
    """
    users = Users.select().where(Users.access_courses_token != '')
    for user in users:
        telegraph = Telegraph(user.access_courses_token)
        response = telegraph.revoke_access_token()
        Users.set_by_id(user.id, {'access_courses_token': response['access_token']})
        bot.send_message(user.chat_id,
                         'Нажмите пожалуйста на кнопку, для проддержания активности Вашего аккаунта. После открытия страницы просто закройте её.',
                         reply_markup=get_auth_table(response['auth_url']))

if __name__ == '__main__':
    update_access_tokens()
