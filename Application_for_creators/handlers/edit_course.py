from telebot.types import Message, CallbackQuery

from Application_for_creators.utils import *
from database.models import Course


@bot.message_handler(func=lambda msg: msg.text == 'Изменить общие данные', is_edit_course=True)
def handle_change_meta_data_1(msg: Message):
    bot.send_message(msg.chat.id, 'Выберите, что хотите изменить', reply_markup=change_meta_data_table)


@bot.callback_query_handler(func=lambda call: 'change' in call.data, is_edit_course=True)
def handle_change_meta_data_2(call: CallbackQuery):
    chat_id = call.message.chat.id
    course_id = get_user_attr(chat_id, 'current_course')
    course = Course.get_by_id(course_id)

    if 'title' in call.data:
        bot.send_message(chat_id, f'Введите новое название (Старое название: `{course.title}`)')
        set_state(chat_id, 'enter_title')
    elif 'description' in call.data:
        bot.send_message(chat_id, f'Введите новое описание (Старое описание: `{course.description}`)')
        set_state(chat_id, 'enter_description')
    elif 'price' in call.data:
        bot.send_message(chat_id, f'Введите новую цену (Старая цена: `{course.price}`)')
        set_state(chat_id, 'enter_price')
    elif 'logo' in call.data:
        bot.send_message(chat_id, f'Отправьте новую фотографию. Вот старое изображение:')
        bot.send_photo(call.message.chat.id, get_image_from_s3('mybacket', f'logos/{course_id}.jpg'))
        set_state(chat_id, 'upload_logo')

    set_user_attr(chat_id, 'action', call.data)


@bot.message_handler(func=lambda msg: msg.text == 'Уроки курса', is_edit_course=True)
def handle_all_lessons(msg: Message):
    order_of_lessons = Course.get_by_id(get_user_attr(msg.chat.id, 'current_course')).order_of_lessons
    if order_of_lessons == '':
        bot.send_message(msg.chat.id, 'В курсе пока нет уроков, Вы можете их добавить нажав на кнопку под сообщением',
                         reply_markup=InlineKeyboardMarkup().add(add_lesson_btn))
    else:
        bot.send_message(msg.chat.id, 'Нажав на урок, вы можете редактировать его содержание или переместить',
                         reply_markup=get_all_lessons_table(order_of_lessons).add(add_lesson_btn))


@bot.message_handler(func=lambda msg: msg.text == 'Добавить урок', is_edit_course=True)
@bot.callback_query_handler(func=lambda call: call.data == 'add_lesson', is_edit_course=True)
def handle_edit_lesson(msg):
    if not hasattr(msg, 'chat'):  # Если msg это на самом деле callback ответ
        msg = msg.message

    user = Users.select().where(Users.chat_id == msg.chat.id)[0]
    telegraph = Telegraph(user.access_courses_token)
    new_page = telegraph.create_page('Название', html_content='Контент')
    current_course_id = get_user_attr(msg.chat.id, 'current_course')
    new_lesson = Lesson.create(
        user_id=user.id,
        course_id=current_course_id,
        url=new_page['url']
    )
    query = Course\
        .update({Course.order_of_lessons: Course.order_of_lessons + str(new_lesson.get_id()) + ' '})\
        .where(Course.id == current_course_id)
    query.execute()

    # set_user_attr(msg.chat.id, 'new_lesson_url', new_page['url'])

    bot.send_message(msg.chat.id, '<Какая-то инструкция>. После окончания редактирования обязательно нажмите "Publish"',
                     reply_markup=get_edit_lesson_table(new_page['url']))


@bot.callback_query_handler(func=lambda call: call.data.startswith('lesson'), is_edit_course=True)
def handle_choose_lesson(call: CallbackQuery):
    order_of_lessons = Course.get_by_id(get_user_attr(call.message.chat.id, 'current_course')).order_of_lessons
    lesson_index = int(call.data.split('_')[1])
    lesson_id = order_of_lessons.split()[lesson_index]

    markup = get_all_lessons_table(order_of_lessons)
    edit_btn = get_edit_btn(Lesson.get_by_id(lesson_id).url)
    move_btn = InlineKeyboardButton('Переместить', callback_data=f'move_{lesson_index}')
    delete_btn = InlineKeyboardButton('Удалить', callback_data=f'delete_{lesson_id}')
    markup.row(edit_btn, move_btn, delete_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)

# @bot.callback_query_handler(func=lambda call: 'save_lesson')
# def handle_save_lesson(msg: Message):
#     url = get_user_attr(msg.chat.id, 'new_lesson_url')
