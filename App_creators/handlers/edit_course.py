from telebot.types import Message, CallbackQuery

from App_creators.tables import *
from App_creators.utils import *
from App_main.utils import standard_date_to_excel_date
from database.models import Course, Lesson, Topics, UserCourse
from datetime import datetime

@bot.message_handler(func=lambda msg: msg.text == 'Изменить общие данные', is_edit_course=True)
def handle_change_meta_data_1(msg: Message):
    """
    Первый этап изменения общих данных о курсе
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, 'Выберите, что хотите изменить', reply_markup=change_meta_data_table)


@bot.callback_query_handler(func=lambda call: 'change' in call.data, is_edit_course=True)
def handle_change_meta_data_2(call: CallbackQuery):
    """
    Второй этап изменения общих данных о курсе
    :param call: Входящий callback запрос
    """
    chat_id = call.message.chat.id
    course_id = get_user_attr(chat_id, 'current_course')
    course = Course.get_by_id(course_id)
    msg_id = call.message.message_id
    if 'title' in call.data:
        bot.edit_message_text(f'Введите новое название (Старое название: `{course.title}`)',
                              chat_id=chat_id, message_id=msg_id, reply_markup=None)
        set_state(chat_id, 'enter_title')
    elif 'description' in call.data:
        bot.edit_message_text(f'Введите новое описание (Старое описание: `{course.description}`)',
                              chat_id=chat_id, message_id=msg_id, reply_markup=None)
        set_state(chat_id, 'enter_description')
    elif 'price' in call.data:
        bot.edit_message_text(
            f'Введите новую цену (>= 2 рублей) или нажмите /free, чтобы сделать его бесплатным (Старая цена: `{course.price}`)',
            chat_id=chat_id, message_id=msg_id, reply_markup=None)
        set_state(chat_id, 'enter_price')
    elif 'logo' in call.data:
        try:
            img = get_image_from_s3('mybacket', f'logos/{course_id}.jpg')
            bot.edit_message_text(f'Отправьте новую фотографию. Вот старое изображение:',
                                  chat_id=chat_id, message_id=msg_id, reply_markup=None)
            bot.send_photo(call.message.chat.id, img)
            set_state(chat_id, 'upload_logo')
        except:
            bot.edit_message_text(
                f'Отправьте квадратную фотографию. Она будет видна клиенту вместе с названием и описанием.',
                chat_id=chat_id, message_id=msg_id, reply_markup=None)
            set_state(chat_id, 'upload_logo')
    elif 'topic' in call.data:
        if course.topic_id:
            topic_text = Topics.get_by_id(course.topic_id).text
            txt = f'Выберите новую сферу, по которой у Вас будет курс. Старая сфера: {topic_text} (Если вы хотите добавить ещё какую-то сферу жизни в этот список, напишите об этом в отзыве)'
        else:
            txt = f'Выберите сферу, по которой у Вас будет курс. (Если вы хотите добавить ещё какую-то сферу жизни в этот список, напишите об этом в отзыве)'
        bot.edit_message_text(txt, chat_id=chat_id, message_id=msg_id, reply_markup=topics_table)
        set_state(chat_id, 'choose_topic')

    set_user_attr(chat_id, 'action', call.data)


@bot.message_handler(func=lambda msg: msg.text == 'Удалить курс', is_edit_course=True)
def handle_delete_course(msg: Message):
    """
    Хэндлер удаления курса
    :param msg: Входящее сообщение
    """
    markup = InlineKeyboardMarkup()
    btn_yes = InlineKeyboardButton('Да', callback_data='confirmation_delete_course_yes')
    btn_no = InlineKeyboardButton('Нет', callback_data='confirmation_delete_course_no')
    markup.row(btn_yes, btn_no)
    bot.send_message(msg.chat.id, 'Вы уверены, что хотите это сделать? Действие нельзя будет отменить',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmation_delete_course'), is_edit_course=True)
def handle_confirmation_delete_course(call: CallbackQuery):
    """
    Хэндлер подтверждения, что пользователь хочет удалить курс
    :param call: Входящий callback запрос
    """
    if 'yes' in call.data:
        current_course_id = get_user_attr(call.message.chat.id, 'current_course')
        del_lessons = Lesson.delete().where(Lesson.course_id == current_course_id)
        del_records = UserCourse.delete().where(UserCourse.course_id == current_course_id)
        del_lessons.execute()
        del_records.execute()

        Course.delete_by_id(current_course_id)
        bot.edit_message_text('Курс был успешно удалён!',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=None)
        bot.send_message(call.message.chat.id, 'Создайте новый курс, у Вас обязательно получится',
                         reply_markup=start_table)
        set_user_attr(call.message.chat.id, 'current_course', '')
    else:
        bot.edit_message_text('Дейсвие отменено, курс не удалён',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=None)


@bot.message_handler(commands=['postpone'])
def postpone_card_input(msg):
    """
    Хэндлер отвечает за откладываение загрузки номера карты в систему
    :param msg: Входящее сообщение
    """
    delete_state(msg.chat.id)
    bot.send_message(msg.chat.id, 'Когда будете готовы загрузить, нажмите кнопку "Опубликовать курс в интрнет" снова')


@bot.message_handler(func=lambda msg: msg.text == 'Опубликовать курс в интернет', is_edit_course=True)
def handle_publish_course(msg: Message):
    """
    Хэндлер публикации курса в интернет
    :param msg: Входящее сообщение
    """
    course = Course.get_by_id(get_user_attr(msg.chat.id, 'current_course'))
    user = Users.get_by_id(course.user_id)
    if not user.bank_card and course.price != 0:
        bot.send_message(msg.chat.id, 'Так как вы сделали курс платным, то Вам нужно:'
                                      '\n1. Зайти на сайт https://yoomoney.ru/'
                                      '\n2. Зарегистрироваться там'
                                      '\n3. Отправить номер созданного кошелька без пробелов следующим сообщением  (именно кошелька)'
                                      '\nИли вы можете нажать /postpone и загрузить номер позже'
                                      '\nПримите к сведению, что за каждого записавшегося на курс Вам будет приходить не полная стоимость курса, а стоимость курса минус небольшая комиссия')

        set_state(msg.chat.id, 'enter_bank_card')
        return

    bot.send_message(msg.chat.id, 'Ваш курс станет доступным пользователям после проверки администратора')
    markup = get_all_lessons_table(course.order_of_lessons, for_creator=False)
    btn_publish = InlineKeyboardButton('Опубликовать', callback_data=f'publish_course_{course.id}')
    btn_reject = InlineKeyboardButton('Отправить на доработку', callback_data=f'reject_course_{course.id}')
    markup.row(btn_publish, btn_reject)
    bot.send_message(values['MAINTAINER_CHAT_ID'], 'Создан новый курс, проверьте его на адекватность\n'
                                                   f'Название - {course.title}\n'
                                                   f'Описание - {course.description}', reply_markup=markup)


@bot.message_handler(state='enter_bank_card', func=lambda msg: check_bank_card(msg.text), is_edit_course=True)
def handle_enter_correct_bank_card(msg: Message):
    """
    Хэндлер корректного ввода номера кошелька пользователя
    :param msg: Входящее сообщение
    """
    query = Users.update({'bank_card': msg.text}).where(Users.chat_id == msg.chat.id)
    query.execute()
    delete_state(msg.chat.id)
    handle_publish_course(msg)


@bot.message_handler(state='enter_bank_card', func=lambda msg: not check_bank_card(msg.text), is_edit_course=True)
def handle_enter_incorrect_bank_card(msg: Message):
    """
    Хэндлер некорректного ввода номера кошелька пользователя
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, 'Некорректный номер кошелька. Введите число с как минимум 16 знаками')


@bot.callback_query_handler(func=lambda call: call.data.startswith('publish_course'), is_edit_course=True)
def handle_confirm_publishing(call: CallbackQuery):
    """
    Хэндлер подтверждения со стороны администратора, что курс адекватный
    :param call: Входящий callback запрос
    """
    course = Course.get_by_id(int(call.data.split('_')[-1]))
    current_date = datetime.now().date()
    Course.set_by_id(course.id, {'publication_date': standard_date_to_excel_date(current_date)})
    chat_id = Users.get_by_id(course.user_id).chat_id
    bot.send_message(chat_id, f'Теперь Ваш курс "{course.title}" доступен в интернете!',
                     reply_markup=get_edit_course_table(call.message.chat.id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_course'), is_edit_course=True)
def handle_reject_publishing(call: CallbackQuery):
    """
    Хэндлер отклонения администратором публикации курса вследствие несоответствия названия и описания содержанию или
     наличия в нём запрещённого контента
    :param call: Входящий callback запрос
    """
    bot.edit_message_text(
        'Введите Ваш комментарий по поводу того, что не так в этом курсе. Он будет передан создателю курса',
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    course = Course.get_by_id(int(call.data.split('_')[-1]))
    bot.register_next_step_handler(call.message, enter_course_flaws, course)


def enter_course_flaws(msg, course):
    """
    Функция ввода недостатков курса
    :param msg: Входящее сообщение
    :param course: Курс, который отклонили
    """
    chat_id = Users.get_by_id(course.user_id).chat_id
    bot.send_message(chat_id, f'Публикация Вашего курса "{course.title}" была отклонена\nКомментарий:\n{msg.text}\n\n'
                              f'Отредактируйте курс и отправьте запрос на публикацию снова')


@bot.message_handler(func=lambda msg: msg.text == 'Уроки курса', is_edit_course=True)
def handle_all_lessons(msg: Message, is_edit_current_msg=False):
    """
    Хэндлер вывода всех уроков курса
    :param msg: Входящее сообщение
    """
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
            bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id,
                                  reply_markup=markup.add(add_lesson_btn))
        else:
            bot.send_message(msg.chat.id, text, reply_markup=markup.add(add_lesson_btn))


@bot.message_handler(func=lambda msg: msg.text == 'Добавить урок', is_edit_course=True)
@bot.callback_query_handler(func=lambda call: call.data == 'add_lesson', is_edit_course=True)
def handle_add_lesson(msg):
    """
    Хэндлер добавления нового урока в курс
    :param msg: Входящее сообщение
    """
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
    query = Course \
        .update({Course.order_of_lessons: Course.order_of_lessons + ' ' + str(new_lesson.get_id())}) \
        .where(Course.id == current_course_id)
    query.execute()

    # set_user_attr(msg.chat.id, 'new_lesson_url', new_page['url'])

    bot.send_message(msg.chat.id,
                     'В интерфейсе вы можете загружать текстовые материалы, фото, ссылки на видео или сторонние сервисы. После окончания редактирования обязательно нажмите "Publish"',
                     reply_markup=get_edit_lesson_table(new_page['url']))


@bot.callback_query_handler(func=lambda call: call.data.startswith('lesson'), is_edit_course=True)
def handle_choose_lesson(call: CallbackQuery):
    """
    Хэндлер выбора урока для его редактирования
    :param call: Входящий callback запрос
    """
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id)
    lesson_index = int(call.data.split('_')[1])
    lesson_id = order_of_lessons.split()[lesson_index]
    set_user_attr(call.message.chat.id, 'current_lesson', lesson_index)

    markup = get_all_lessons_table(order_of_lessons)
    edit_btn = get_edit_btn(Lesson.get_by_id(lesson_id).url)
    move_btn = InlineKeyboardButton('Переместить', callback_data=f'move_{lesson_index}')
    delete_btn = InlineKeyboardButton('Удалить', callback_data=f'delete_lesson_{lesson_index}')
    markup.row(edit_btn, move_btn, delete_btn)
    try:
        bot.edit_message_reply_markup(call.message.chat.id,
                                      message_id=call.message.id,
                                      reply_markup=markup)
    except:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('move'), is_edit_course=True)
def handle_move_lesson_1(call: CallbackQuery):
    """
    Хэндлер обработки желания пользователя поменять местами уроки курса
    :param call: Входящий callback запрос
    """
    lesson_index = int(call.data.split('_')[1])
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id)

    markup = get_moving_lesson_table(call.message.chat.id, order_of_lessons, lesson_index, 0)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('swap'), is_edit_course=True)
def handle_move_lesson_2(call: CallbackQuery):
    """
    Хэндлер обработки кнопок '⬆' и '⬇' для перемещения урока курса вверх или вниз
    :param call: Входящий callback запрос
    """
    order = get_current_order_of_lessons(call.message.chat.id).split()
    lesson_index = get_user_attr(call.message.chat.id, 'current_lesson')
    if 'up' in call.data:
        delta = -1
    elif 'down' in call.data:
        delta = 1

    order[lesson_index + delta], order[lesson_index] = order[lesson_index], order[lesson_index + delta]
    order = ' '.join(order)
    Course.set_by_id(get_user_attr(call.message.chat.id, 'current_course'), {'order_of_lessons': order})

    set_user_attr(call.message.chat.id, 'current_lesson', lesson_index + delta)
    markup = get_moving_lesson_table(call.message.chat.id, order, lesson_index, delta)
    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'save_order', is_edit_course=True)
def handle_save_order(call: CallbackQuery):
    """
    Хэндлер сохранения порядка уроков в курсе
    :param call: Входящий callback запрос
    """
    markup = InlineKeyboardMarkup().de_json(get_user_attr(call.message.chat.id, 'all_lessons_table'))
    bot.edit_message_reply_markup(call.message.chat.id,
                                  message_id=call.message.id,
                                  reply_markup=markup.add(add_lesson_btn))


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_lesson'), is_edit_course=True)
def handle_delete_lesson(call: CallbackQuery):
    """
    Хэндлер удаления урока из курса
    :param call: Входящий callback запрос
    """
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
    """
    Хэндлер подтверждения, что пользователь хочет удалить урок из курса
    :param call: Входящий callback запрос
    """
    if 'yes' in call.data:
        lesson_index = get_user_attr(call.message.chat.id, 'current_lesson')
        order = get_current_order_of_lessons(call.message.chat.id).split()
        # Delete lesson
        Lesson.delete_by_id(order[lesson_index])
        # Update course order of lessons
        order = order[:lesson_index] + order[lesson_index + 1:]

        Course.set_by_id(get_user_attr(call.message.chat.id, 'current_course'), {'order_of_lessons': ' '.join(order)})

    handle_all_lessons(msg=call.message, is_edit_current_msg=True)
