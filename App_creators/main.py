from datetime import datetime

from App_creators.handlers.create_course import *
from App_creators.tables import get_auth_table, edit_course_table, get_all_courses_table


@bot.message_handler(commands=['start'])
def handle_start(msg):
    is_registered = Users.select().where(Users.chat_id == msg.chat.id)
    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)

    if not is_registered:
        telegraph = Telegraph()
        response = telegraph.create_account(short_name='Teach&Learn tutor')
        # Сделать может быть ввод номера карты пользователя
        bot.send_message(msg.chat.id, 'Для регистрации нажмите на кнопку. После открытия страницы просто закройте её.',
                         reply_markup=get_auth_table(response['auth_url']))
        Users.create(chat_id=msg.chat.id, access_courses_token=response['access_token'])


@bot.message_handler(func=lambda msg: msg.text == 'Посмотреть мои курсы')
def handle_show_my_courses(msg: Message):
    courses = Course.select().join(Users).where(Users.chat_id == msg.chat.id)
    if not courses:
        bot.send_message(msg.chat.id, 'У вас пока нет курсов')
        return
    bot.send_message(msg.chat.id, 'Вот ваши курсы:', reply_markup=get_all_courses_table(courses))


@bot.callback_query_handler(func=lambda call: call.data.startswith('course'))
def handle_choose_course(call: CallbackQuery):
    set_user_attr(call.message.chat.id, 'current_course', int(call.data.split('_')[1]))
    bot.send_message(call.message.chat.id, 'Вы в меню курса', reply_markup=edit_course_table)


@bot.message_handler(func=lambda msg: msg.text == 'Назад')
def handle_back(msg: Message):
    set_user_attr(msg.chat.id, 'current_course', '')
    bot.send_message(msg.chat.id, 'Вы в меню курса', reply_markup=start_table)


@bot.message_handler(content_types=['text', 'photo', 'video', 'file'])
def handle_strange_msg(msg: Message):
    bot.send_message(msg.chat.id, 'Я Вас не понимаю, лучше нажми на одну из кнопочек снизу')


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.add_custom_filter(StateFilter())
    bot.add_custom_filter(EditingCourseFilter())
    bot.infinity_polling()
