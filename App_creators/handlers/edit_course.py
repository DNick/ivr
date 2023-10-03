from telebot.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegraph import Telegraph

from App_creators.tables import get_all_lessons_table, get_edit_btn, get_moving_lesson_table, add_lesson_btn, \
    get_edit_lesson_table, change_meta_data_table
from App_creators.utils import *
from database.models import Course, Lesson


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
def handle_all_lessons(msg: Message, is_edit_current_msg=False):
    order_of_lessons = get_current_order_of_lessons(msg.chat.id)
    if order_of_lessons == '':
        text = 'В курсе пока нет уроков, Вы можете их добавить нажав на кнопку под сообщением'
        markup = InlineKeyboardMarkup().add(add_lesson_btn)
        if is_edit_current_msg:
            bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id, reply_markup=markup)
        else:
            bot.send_message(msg.chat.id, text, reply_markup=markup)
    else:
        text = 'Нажав на урок, вы можете редактировать его содержание или переместить'
        markup = get_all_lessons_table(order_of_lessons)
        set_user_attr(msg.chat.id, 'all_lessons_table', markup.to_json())
        if is_edit_current_msg:
            bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id, reply_markup=markup.add(add_lesson_btn))
        else:
            bot.send_message(msg.chat.id, text, reply_markup=markup.add(add_lesson_btn))


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
        .update({Course.order_of_lessons: Course.order_of_lessons + ' ' + str(new_lesson.get_id())})\
        .where(Course.id == current_course_id)
    query.execute()

    # set_user_attr(msg.chat.id, 'new_lesson_url', new_page['url'])

    bot.send_message(msg.chat.id, '<Какая-то инструкция>. После окончания редактирования обязательно нажмите "Publish"',
                     reply_markup=get_edit_lesson_table(new_page['url']))


@bot.callback_query_handler(func=lambda call: call.data.startswith('lesson'), is_edit_course=True)
def handle_choose_lesson(call: CallbackQuery):
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id)
    lesson_index = int(call.data.split('_')[1])
    lesson_id = order_of_lessons.split()[lesson_index]
    set_user_attr(call.message.chat.id, 'current_lesson', lesson_index)

    markup = get_all_lessons_table(order_of_lessons)
    edit_btn = get_edit_btn(Lesson.get_by_id(lesson_id).url)
    move_btn = InlineKeyboardButton('Переместить', callback_data=f'move_{lesson_index}')
    delete_btn = InlineKeyboardButton('Удалить', callback_data=f'delete_lesson_{lesson_index}')
    markup.row(edit_btn, move_btn, delete_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('move'), is_edit_course=True)
def handle_move_lesson_1(call: CallbackQuery):
    lesson_index = int(call.data.split('_')[1])
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id)

    markup = get_moving_lesson_table(call.message.chat.id, order_of_lessons, lesson_index, 0)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('swap'), is_edit_course=True)
def handle_move_lesson_2(call: CallbackQuery):
    order = get_current_order_of_lessons(call.message.chat.id).split()
    lesson_index = get_user_attr(call.message.chat.id, 'current_lesson')
    if 'up' in call.data:
        delta = -1
    elif 'down' in call.data:
        delta = 1

    order[lesson_index + delta], order[lesson_index] = order[lesson_index], order[lesson_index + delta]
    order = ' '.join(order)
    Course.set_by_id(get_user_attr(call.message.chat.id, 'current_course'), {'order_of_lessons': order})

    set_user_attr(call.message.chat.id, 'move_lesson', lesson_index + delta)
    markup = get_moving_lesson_table(call.message.chat.id, order, lesson_index, delta)
    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'save_order', is_edit_course=True)
def handle_save_order(call: CallbackQuery):
    markup = InlineKeyboardMarkup().de_json(get_user_attr(call.message.chat.id, 'all_lessons_table'))
    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup.add(add_lesson_btn))

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_lesson'), is_edit_course=True)
def handle_delete_lesson(call: CallbackQuery):
    order = get_current_order_of_lessons(call.message.chat.id)
    markup = get_all_lessons_table(order)
    btn_confirmation = InlineKeyboardButton('Вы уверены что хотите это сделать?', callback_data=' ')
    btn_yes = InlineKeyboardButton('Да', callback_data='confirmation_delete_lesson_yes')
    btn_no = InlineKeyboardButton('Нет', callback_data='confirmation_delete_lesson_no')
    markup.add(btn_confirmation)
    markup.row(btn_yes, btn_no)
    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmation_delete_lesson'), is_edit_course=True)
def handle_confirmation_delete_lesson(call: CallbackQuery):
    if 'yes' in call.data:
        lesson_index = get_user_attr(call.message.chat.id, 'current_lesson')
        order = get_current_order_of_lessons(call.message.chat.id).split()
        # Delete lesson
        Lesson.delete_by_id(order[lesson_index])
        # Update course order of lessons
        order = order[:lesson_index] + order[lesson_index + 1:]

        Course.set_by_id(get_user_attr(call.message.chat.id, 'current_course'), {'order_of_lessons': ' '.join(order)})

    handle_all_lessons(msg=call.message, is_edit_current_msg=True)
    #
    # order = get_current_order_of_lessons(call.message.chat.id)
    # bot.edit_message_reply_markup(call.message.chat.id,
    #                               message_id=call.message.id,
    #                               reply_markup=get_all_lessons_table(order).add(add_lesson_btn))


# @bot.callback_query_handler(func=lambda call: 'save_lesson')
# def handle_save_lesson(msg: Message):
#     url = get_user_attr(msg.chat.id, 'new_lesson_url')
