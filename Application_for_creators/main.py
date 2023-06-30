from datetime import datetime

from telebot.custom_filters import StateFilter
from telebot.types import Message
from telebot.handler_backends import State, StatesGroup

from Application_for_creators.utils import is_non_negative_digit
from tables import *
from config import bot


class MyStates(StatesGroup):
    enter_title = State()
    enter_description = State()
    enter_price = State()


@bot.message_handler(commands=['start'])
def handle_start(msg):
    telegraph = Telegraph()
    response = telegraph.create_account(short_name='Teach&Learn course')
    # Сделать может быть ввод номера карты пользователя
    Users.create(chat_id=msg.chat.id, access_courses_token=response['access_token'], auth_url=response['auth_url'])

    bot.send_message(msg.chat.id, 'Привет! Я бот такой-то делаю то-то', reply_markup=start_table)


@bot.message_handler(func=lambda msg: msg.text == 'Создать свой курс')
def handle_create_course(msg: Message):
    bot.set_state(msg.from_user.id, MyStates.enter_title, msg.chat.id)
    bot.send_message(msg.chat.id, 'Введите название курса (потом можно будет его поменять)',
                     reply_markup=exit_and_not_save_table)


@bot.message_handler(state="*", func=lambda msg: msg.text == 'Выйти и не сохранить')
def exit_and_not_save(msg):
    bot.send_message(msg.chat.id, "Вы в главном меню", reply_markup=start_table)
    bot.delete_state(msg.from_user.id, msg.chat.id)


@bot.message_handler(state=MyStates.enter_title)
def enter_title(msg):
    bot.send_message(msg.chat.id, 'Введите подробное описание курса (потом можно будет его поменять)')
    bot.set_state(msg.from_user.id, MyStates.enter_description, msg.chat.id)
    with bot.retrieve_data(msg.from_user.id, msg.chat.id) as data:
        data['title'] = msg.text


@bot.message_handler(state=MyStates.enter_description)
def enter_description(msg):
    bot.send_message(msg.chat.id,
                     'Введите цену вашего курса в рублях (если хотите сделать курс бесплатным, введите "0")')
    bot.set_state(msg.from_user.id, MyStates.enter_price, msg.chat.id)
    with bot.retrieve_data(msg.from_user.id, msg.chat.id) as data:
        data['description'] = msg.text


@bot.message_handler(state=MyStates.enter_price, func=lambda msg: is_non_negative_digit(msg.text))
def enter_correct_price(msg):
    try:
        user_id = Users.select().where(Users.chat_id == msg.chat.id)[0].id
    except:
        bot.send_message(msg.chat.id, 'Вас нет в базе пользователей, нажмите /start, и попробуйте снова')
        return

    with bot.retrieve_data(msg.from_user.id, msg.chat.id) as data:
        Course.create(user_id=user_id,
                      title=data['title'],
                      description=data['description'],
                      price=msg.text)
    bot.send_message(msg.chat.id, 'Курс создан, теперь вы можете добавлять новые темы', )
    bot.delete_state(msg.from_user.id, msg.chat.id)


@bot.message_handler(state=MyStates.enter_price, func=lambda msg: not is_non_negative_digit(msg.text))
def enter_incorrect_price(msg):
    bot.send_message(msg.chat.id, 'Некорректная цена. Введите пожалуйста натуральное число')


@bot.message_handler(func=lambda msg: msg.text == 'Посмотреть мои курсы')
def handle_show_my_courses(msg: Message):
    bot.set_state(msg.from_user.id, 'back_main')


@bot.message_handler(func=lambda msg: True)
def handle_strange_msg(msg):
    bot.send_message(msg.chat.id, 'Я Вас не понимаю, лучше нажми на одну из кнопочек снизу')


# @bot.message_handler(func=lambda msg: 'Назад' in msg.text or 'Выйти и не сохранить' in msg.text)
# def answer(msg):
#     if bot.get_state(msg.from_user.id) == 'back_main':
#         bot.send_message(msg.chat.id, 'Вы в главном меню', reply_markup=start_table)

if __name__ == "__main__":
    print(f"Start polling at {datetime.now()}")
    bot.add_custom_filter(StateFilter(bot))
    bot.infinity_polling()
