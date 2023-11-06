import sys
from datetime import datetime

sys.path.append('../../../')
from telebot.types import Message, CallbackQuery
from yoomoney import Client, Quickpay

from App_creators.tables import get_all_lessons_table
from App_creators.utils import set_user_attr, get_current_order_of_lessons, get_user_attr
from database.models import Users, UserCourse, Course
from tables import *
from config import *


@bot.message_handler(commands=['start'])
def handle_start(msg):
    """
    Начальный хэндлер
    :param msg: Входящее сообщение
    """
    is_registered = Users.select().where(Users.chat_id == msg.chat.id)

    if not is_registered:
        Users.create(chat_id=msg.chat.id)
    bot.send_message(msg.chat.id,
                     'Здравствуйте! Я - бот для прохождения курсов и создания своих собственных. Уверен вы найдёте здесь курс, соответствующий Вашим интересам.',
                     reply_markup=start_table)


@bot.message_handler(func=lambda msg: msg.text == 'Создать курс')
def handle_create(msg: Message):
    """
    Хэндлер перехода в меню создания курсов
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id,
                     'Перейдите по ссылке в меню создания курса: https://t.me/Teach_and_learn_creators_bot')


@bot.message_handler(func=lambda msg: msg.text == 'Мои курсы')
def handle_get_taken_courses(msg: Message):
    """
    Хэндлер получения проходимых курсов
    :param msg: Входящее сообщение
    """
    course_ids = list(map(lambda x: x.course_id, UserCourse.select().join(Users).where(Users.chat_id == msg.chat.id)))
    courses = Course.select().where(Course.id.in_(course_ids))
    if not courses:
        bot.send_message(msg.chat.id, 'Вы пока не получили доступ ни к одному курсу.')
        return
    bot.send_message(msg.chat.id, 'Вот проходимые Вами курсы:', reply_markup=get_all_taken_courses_table(courses))


@bot.callback_query_handler(func=lambda call: call.data.startswith('taken_course'))
def handle_choose_course(call: CallbackQuery):
    """
    Хэндлер просмотра уроков курса
    :param сall: Входящий callback запрос
    """
    course_id = int(call.data.split('_')[2])
    set_user_attr(call.message.chat.id, 'current_course_main', course_id)
    order_of_lessons = get_current_order_of_lessons(call.message.chat.id, for_creator=False)
    chat_url = Course.get_by_id(course_id).chat_url
    add = ''
    if chat_url:
        add = ' Также вы можете войти в беседу проходящих курс по ссылке: ' + chat_url

    if order_of_lessons:
        bot.send_message(call.message.chat.id, 'Вы можете зайти в какой-нибудь урок и подробно изучить тему.' + add,
                         reply_markup=get_all_lessons_table(order_of_lessons, for_creator=False))
    else:
        bot.send_message(call.message.chat.id, 'В этом курсе нет уроков')


@bot.message_handler(func=lambda msg: msg.text == 'Оценить курс')
def handle_rate_course_1(msg: Message):
    """
    Хэндлер первого этапа оценивания курса
    :param msg: Входящее сообщение
    """
    course_ids = list(map(lambda x: x.course_id, UserCourse.select().join(Users).where(Users.chat_id == msg.chat.id)))
    courses = Course.select().where(Course.id.in_(course_ids))
    if not courses:
        bot.send_message(msg.chat.id, 'Вы пока не получили доступ ни к одному курсу.')
        return
    bot.send_message(msg.chat.id, 'Выберите курс, который хотите оценить:',
                     reply_markup=get_all_taken_courses_table(courses, is_rate=True))


@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_course'))
def handle_rate_course_2(call: CallbackQuery):
    """
    Хэндлер второго этапа оценивания курса
    :param сall: Входящий callback запрос
    """
    set_user_attr(call.message.chat.id, 'current_course_main', int(call.data.split('_')[-1]))
    bot.send_message(call.message.chat.id, 'Поставьте оценку курсу от 1 до 10, где 1 - '
                                           '"не рекомендую этот курс никому", а 10 - "я в восторге от качества курса."',
                     reply_markup=rate_course_table)


@bot.callback_query_handler(func=lambda call: call.data.startswith('get_rate_mark'))
def handle_get_rate_mark(call: CallbackQuery):
    """
    Хэндлер записи в базу оценки пользователя
    :param call: Входящий callback запрос
    """
    mark = int(call.data.split('_')[-1])
    current_course_id = get_user_attr(call.message.chat.id, 'current_course_main')
    Course.set_by_id(current_course_id, {Course.rate_sum: Course.rate_sum + mark,
                                         Course.rate_count: Course.rate_count + 1})
    bot.edit_message_text('Спасибо! Ваше мнение важно для нас.', call.message.chat.id,
                          message_id=call.message.message_id, reply_markup=None)


@bot.message_handler(func=lambda msg: msg.text == 'Оставить отзыв')
def handle_give_feedback_1(msg: Message):
    """
    Хэндлер первого этапа оставления отзыва
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, 'Выберите, кому Вы хотите отправить отзыв/жалобу/предложение/вопрос',
                     reply_markup=feedback_for_table)


@bot.callback_query_handler(func=lambda call: call.data.startswith('feedback_for'))
def handle_give_feedback_2(call: CallbackQuery):
    """
    Хэндлер второго этапа оставления отзыва
    :param call: Входящий callback запрос
    """
    destination = call.data.split('_')[-1]
    if destination == 'developers':
        bot.edit_message_text('Напишите Ваш отзыв в одном сообщении и я обязательно передам его разработчикам',
                              chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        bot.register_next_step_handler(call.message, enter_feedback, values['MAINTAINER_CHAT_ID'])
    elif destination == 'creator':
        course_ids = list(
            map(lambda x: x.course_id, UserCourse.select().join(Users).where(Users.chat_id == call.message.chat.id)))
        courses = Course.select().where(Course.id.in_(course_ids))
        bot.edit_message_text('Выберите курс, создателю которого вы хотите послать отзыв',
                              chat_id=call.message.chat.id, message_id=call.message.message_id,
                              reply_markup=get_all_taken_courses_table(courses, is_feedback=True))


@bot.callback_query_handler(func=lambda call: call.data.startswith('give_feedback_creator'))
def handle_give_feedback_creators(call: CallbackQuery):
    """
    Хэндлер третьего этапа оставления отзыва (только для оставления отзыва создателям курсов)
    :param call: Входящий callback запрос
    """
    course = Course.get_by_id(int(call.data.split('_')[-1]))
    chat_id = Users.get_by_id(course.user_id).chat_id
    bot.edit_message_text(
        f'Напишите Ваш отзыв в одном сообщении и я обязательно передам его создателю курса {course.title}',
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    bot.register_next_step_handler(call.message, enter_feedback, chat_id)


def enter_feedback(msg, target_chat_id):
    """
    Хэндлер ввода отзыва/жалобы/предложения
    :param msg: Входящее сообщение
    :param target_chat_id: Chat_id пользователя, которому нужно отправить отзыв
    """
    bot.send_message(target_chat_id, 'Поступил новый отзыв:\n\n' + msg.text)
    bot.send_message(msg.chat.id, 'Спасибо! Вы помогаете делать наш сервис лучше', reply_markup=start_table)


@bot.message_handler(content_types=["web_app_data"])
def enroll_into_course(msg):
    """
    Хэндлер записи на курс
    :param msg: Входящее сообщение
    """
    print(msg.web_app_data.data)
    course = Course.get_by_id(msg.web_app_data.data)
    user = Users.select().where(Users.chat_id == msg.chat.id)[0]

    if course.price == '0':
        UserCourse.create(user_id=user.id, course_id=int(course.id))
        bot.send_message(msg.chat.id, 'Вы успешно записались на курс "' + course.title + '"')
    else:
        label = f'{course.id}_{user.id}'
        payment = Quickpay(
            receiver=values['CARD_NUMBER'],
            quickpay_form="button",
            targets="Оплата курса",
            paymentType="AC",
            sum=course.price,
            label=label
        )
        bot.send_message(msg.chat.id, 'Сначала надо оплатить курс. Как это сделаете нажмите на кнопку ниже',
                         reply_markup=get_pay_course_table(payment.base_url, course.price, label))


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_course'))
def handle_pay_course(call: CallbackQuery):
    """
    Хэндлер оплаты курса
    :param call: Входящий callback запрос
    """
    label = '_'.join(call.data.split('_')[2:])
    token = values['YOOMONEY_TOKEN']
    client = Client(token)
    history = client.operation_history(label=label)
    for operation in history.operations:
        if operation.status == 'success':
            course_id, user_id = map(int, label.split('_'))
            title = Course.get_by_id(course_id).title
            UserCourse.create(user_id=user_id, course_id=course_id)
            bot.edit_message_text('Вы успешно записались на курс "' + title + '"', chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=None)
            break
    else:
        bot.send_message(call.message.chat.id,
                         'Я не нашёл Вашу транзакцию или она была неуспешной. Если я ошибаюсь, напишите об этом в отзыве и я обязательно всё перепроверю.')


@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg):
    bot.send_message(msg.chat.id, 'Я Вас не понимаю, лучше нажмите на одну из кнопочек снизу')


if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.infinity_polling()
