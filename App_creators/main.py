from App_creators.handlers.create_course import *
from App_creators.tables import get_auth_table, get_edit_course_table, get_all_courses_table
from datetime import datetime


@bot.message_handler(commands=['start'])
def handle_start(msg):
    """
    Начальный хэндлер
    :param msg: Входящее сообщение
    """
    user = Users.select().where(Users.chat_id == msg.chat.id)
    bot.send_message(msg.chat.id,
                     'Здравствуйте! Я рад, что Вы решили создать свой собственный курс в нашем сервисе. "Знание существует для того, чтобы его распространять" (Р. Эмерсон).',
                     reply_markup=start_table)

    if not user or not user[0].access_courses_token:
        telegraph = Telegraph()
        response = telegraph.create_account(short_name='Teach&Learn tutor')
        bot.send_message(msg.chat.id, 'Для регистрации нажмите на кнопку. После открытия страницы просто закройте её.',
                         reply_markup=get_auth_table(response['auth_url']))
        if not user:
            Users.create(chat_id=msg.chat.id, access_courses_token=response['access_token'])
        else:
            query = (Users.update({'access_courses_token': response['access_token']})
                     .where(Users.chat_id == msg.chat.id))
            query.execute()


@bot.message_handler(func=lambda msg: msg.text == 'Посмотреть мои курсы')
def handle_show_my_courses(msg: Message):
    """
    Хэндлер вывода созданных определённым пользователем курсов
    :param msg: Входящее сообщение
    """
    courses = Course.select().join(Users).where(Users.chat_id == msg.chat.id)
    if not courses:
        bot.send_message(msg.chat.id, 'У вас пока нет курсов')
        return
    bot.send_message(msg.chat.id, 'Вот ваши курсы:', reply_markup=get_all_courses_table(courses))


@bot.callback_query_handler(func=lambda call: call.data.startswith('course'))
def handle_choose_course(call: CallbackQuery):
    """
    Хэндлер выбора курса для редактирования
    :param msg: Входящее сообщение
    """
    course_id = int(call.data.split('_')[1])
    set_user_attr(call.message.chat.id, 'current_course', course_id)
    bot.send_message(call.message.chat.id, f'Вы в меню курса "{Course.get_by_id(course_id).title}"',
                     reply_markup=get_edit_course_table(call.message.chat.id))


@bot.message_handler(func=lambda msg: msg.text == 'Назад')
def handle_back(msg: Message):
    """
    Хэндлер кнопки выхода в главное меню
    :param msg: Входящее сообщение
    """
    set_user_attr(msg.chat.id, 'current_course', '')
    bot.send_message(msg.chat.id, 'Вы в главном меню', reply_markup=start_table)


@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg: Message):
    """
    Хэндлер обработки сообщения, которое бот не понимает
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, 'Я Вас не понимаю, лучше нажмите на одну из кнопочек снизу')


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.add_custom_filter(StateFilter())
    bot.add_custom_filter(EditingCourseFilter())
    bot.infinity_polling()
