import sys

from App_creators.handlers.edit_course import *
from App_creators.tables import exit_and_not_save_table, start_table, yes_no_table, topics_table

sys.path.append('../../')

@bot.message_handler(func=lambda msg: msg.text == 'Создать свой курс')
def handle_create_course(msg: Message):
    set_user_attr(msg.chat.id, 'state', 'enter_title')
    bot.send_message(msg.chat.id, 'Введите название курса (потом можно будет его поменять)',
                     reply_markup=exit_and_not_save_table)


@bot.message_handler(func=lambda msg: msg.text == 'Выйти и не сохранить')
def exit_and_not_save(msg):
    bot.send_message(msg.chat.id, "Вы в главном меню", reply_markup=start_table)
    bot.delete_state(msg.from_user.id, msg.chat.id)


@bot.message_handler(commands=['skip'])
def skip_step(msg):
    current_state = get_state(msg.chat.id)
    if current_state == 'choose_topic':
        bot.send_message(msg.chat.id,
                         'Отправьте квадратную фотографию или нажмите /skip, чтобы пропустить этот шаг. Она будет видна клиенту вместе с названием и описанием.')
        set_state(msg.chat.id, 'upload_logo')
        set_user_attr(msg.chat.id, 'topic', '')
    if current_state == 'upload_logo':
        save_course(msg)


@bot.message_handler(state='enter_title')
def enter_title(msg):
    action = get_user_attr(msg.chat.id, 'action')
    if action != 'change_title':
        bot.send_message(msg.chat.id, 'Введите подробное описание курса (потом можно будет его поменять)')
        set_state(msg.chat.id, 'enter_description')
        set_user_attr(msg.chat.id, 'title', msg.text)
    else:
        bot.send_message(msg.chat.id, 'Название успешно изменено')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'title': msg.text})


@bot.message_handler(state='enter_description')
def enter_description(msg):
    action = get_user_attr(msg.chat.id, 'action')
    if action != 'change_description':
        bot.send_message(msg.chat.id,
                         'Введите цену вашего курса в рублях (если хотите сделать курс бесплатным, введите "0")')
        set_state(msg.chat.id, 'enter_price')
        set_user_attr(msg.chat.id, 'description', msg.text)
    else:
        bot.send_message(msg.chat.id, 'Описание успешно изменено')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'description': msg.text})


@bot.message_handler(state='enter_price', func=lambda msg: is_non_negative_digit(msg.text))
def enter_correct_price(msg):
    action = get_user_attr(msg.chat.id, 'action')
    if action != 'change_price':
        bot.send_message(msg.chat.id,
                         'Выберите тему, по которой вы собираетесь сделать ваш курс или нажмите /skip, чтобы пропустить этот шаг. (Если вы хотите добавить ещё какую-то сферу жизни в этот список, напишите об этом в отзвыве)',
                         reply_markup=topics_table)
        set_state(msg.chat.id, 'choose_topic')
        set_user_attr(msg.chat.id, 'price', msg.text)
    else:
        bot.send_message(msg.chat.id, 'Цена успешно изменена')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'price': msg.text})


@bot.message_handler(state='enter_price', func=lambda msg: not is_non_negative_digit(msg.text))
def enter_incorrect_price(msg):
    bot.send_message(msg.chat.id, 'Некорректная цена. Введите пожалуйста натуральное число')


@bot.callback_query_handler(state='choose_topic', func=lambda call: 'topic' in call.data)
def choose_topic(call):
    chosen_topic = call.data.split('_')[1]
    bot.edit_message_text(f'Вы выбрали тему "{chosen_topic}"', call.message.chat.id, message_id=call.message.id,
                          reply_markup=None)
    set_user_attr(call.message.chat.id, 'topic', chosen_topic)
    bot.send_message(call.message.chat.id,
                     'Отправьте квадратную фотографию или нажмите /skip, чтобы пропустить этот шаг. Она будет видна клиенту вместе с названием и описанием.')
    set_state(call.message.chat.id, 'upload_logo')


@bot.message_handler(state='upload_logo', content_types=['photo', 'file']) # Файлы пока не обрабатываются. Сделать проверку на тип файла надо будет сделать
def upload_logo(msg: Message):
    file_id = msg.photo[-1].file_id
    if is_image_square(file_id):
        save_course(msg, file_id)
    else:
        logo = crop_photo_to_square(file_id)
        bot.send_message(msg.chat.id, 'Устраивает ли вас такая фотография?')
        bot.send_photo(msg.chat.id, logo, reply_markup=yes_no_table)
    set_user_attr(msg.chat.id, 'file_id', file_id)


@bot.callback_query_handler(state='upload_logo', func=lambda call: 'choice' in call.data)
def logo_confirmation(call):
    if 'yes' in call.data:
        save_course(call.message, get_user_attr(call.message.chat.id, 'file_id'))
    else:
        bot.send_message(call.message.chat.id,
                         'Загрузите новую фотографию или нажмите /skip, чтобы пропустить этот шаг.')
