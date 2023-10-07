import sys
from datetime import datetime
sys.path.append('../../../')
from telebot.types import Message, InlineQueryResultArticle, CallbackQuery

from App_creators.tables import get_all_lessons_table
from App_creators.utils import set_user_attr, get_current_order_of_lessons
from database.models import Users, UserCourse, Course
from tables import *
from config import *


@bot.message_handler(commands=['start'])
def handle_start(msg):
    print(msg.chat.id)
    Users.create(chat_id=msg.chat.id)
    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)


# @bot.message_handler(func=lambda msg: msg.text == 'Найти подходящий курс')
# def handle_find(msg: Message):
#     bot.send_message(msg.chat.id, 'Зайдите в каталог', reply_markup=topics_table)
#     bot.send_message(msg.chat.id, 'или выйдите назад', reply_markup=back_table)


@bot.message_handler(func=lambda msg: msg.text == 'Создать курс')
def handle_create(msg: Message):
    bot.send_message(msg.chat.id, 'Перейдите по ссылке в меню создания курса: https://t.me/Teach_and_learn_creators_bot')

@bot.message_handler(func=lambda msg: msg.text == 'Мои курсы')
def handle_get_taken_courses(msg: Message):
    course_ids = list(map(lambda x: x.course_id, UserCourse.select().join(Users).where(Users.chat_id == msg.chat.id)))
    courses = Course.select().where(Course.id.in_(course_ids))
    if not courses:
        bot.send_message(msg.chat.id, 'Вы пока не получили доступ ни к одному курсу.')
        return
    bot.send_message(msg.chat.id, 'Вот ваши курсы:', reply_markup=get_all_taken_courses_table(courses))


@bot.callback_query_handler(func=lambda call: call.data.startswith('taken_course'))
def handle_choose_course(call: CallbackQuery):
    set_user_attr(call.message.chat.id, 'current_course', int(call.data.split('_')[2]))
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id)
    if order_of_lessons:
        bot.send_message(call.message.chat.id, 'Вы можете зайти в какой-нибудь урок и подробно изучить тему',
                         reply_markup=get_all_lessons_table(order_of_lessons, for_creator=False))
    else:
        bot.send_message(call.message.chat.id, 'В этом курсе нет уроков')


@bot.message_handler(func=lambda msg: msg.text == 'Оставить отзыв')
def handle_give_feedback(msg: Message):
    bot.send_message(msg.chat.id, 'Напишите Ваш отзыв в одном сообщении и я обязательно передам его разработчикам')
    bot.register_next_step_handler(msg, enter_feedback)


def enter_feedback(msg):
    bot.send_message(values['MAINTAINER_CHAT_ID'], 'Поступил новый отзыв:\n\n' + msg.text)
    bot.send_message(msg.chat.id, 'Спасибо! Вы помогаете делать наш сервис лучше')


@bot.message_handler(content_types=["web_app_data"])
def enroll_into_course(web_msg):
   user_id = Users.select().where(Users.chat_id == web_msg.chat.id)[0].id
   UserCourse.create(user_id=user_id, course_id=int(web_msg.web_app_data.data))
   course_title = Course.get_by_id(web_msg.web_app_data.data).title
   bot.send_message(web_msg.chat.id, 'Вы успешно записались на курс "' + course_title + '"')


@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg):
    bot.send_message(msg.chat.id, 'Я тебя не понимаю, лучше нажми на одну из кнопочек снизу')

# @bot.callback_query_handler(func=lambda call: 'back' in call.data)
# def answer(call):
#     if call.data == 'back_start_menu':
#         bot.send_message(call.message.chat.id, 'Вы в главном меню', reply_markup=start_table)


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.infinity_polling()
