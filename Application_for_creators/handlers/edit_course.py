from telebot.types import Message, CallbackQuery

from Application_for_creators.utils import *
from database.models import Course


@bot.message_handler(func=lambda msg: msg.text == 'Изменить общие данные')
def handle_change_meta_data_1(msg: Message):
    bot.send_message(msg.chat.id, 'Выберите, что хотите изменить', reply_markup=change_meta_data_table)


@bot.callback_query_handler(func=lambda call: 'change' in call.data)
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
