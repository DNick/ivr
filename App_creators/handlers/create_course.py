from App_creators.handlers.edit_course import *
from App_creators.tables import exit_and_not_save_table, start_table, yes_no_table, topics_table
from database.models import Topics

sys.path.append('../../')


@bot.message_handler(func=lambda msg: msg.text == 'Создать свой курс')
def handle_create_course(msg: Message):
    """
    Хэндлер первого этапа создания курса
    :param msg: Входящее сообщение
    """
    set_user_attr(msg.chat.id, 'state', 'enter_title')
    set_user_attr(msg.chat.id, 'action', 'calm')
    bot.send_message(msg.chat.id, 'Введите название курса (потом можно будет его поменять)',
                     reply_markup=exit_and_not_save_table)


@bot.message_handler(func=lambda msg: msg.text == 'Выйти и не сохранить')
def exit_and_not_save(msg):
    """
    Хэндлер отмены создания курса с несохранением введённых данных
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, "Вы в главном меню", reply_markup=start_table)
    bot.delete_state(msg.from_user.id, msg.chat.id)
    set_state(msg.chat.id, 'calm')


@bot.message_handler(commands=['skip'])
def skip_step(msg):
    """
    Хэндлер пропускания какого-то этапа ввода данных о создающемся курсе
    :param msg: Входящее сообщение
    """
    current_state = get_state(msg.chat.id)
    if current_state == 'choose_topic':
        bot.send_message(msg.chat.id,
                         'Создайте группу в Telegram, и пришлите ссылку на неё или пока пропустите этот шаг, нажав /skip. Все клиенты Вашего курса смогут в неё войти и обсуждать интересные темы.')
        set_state(msg.chat.id, 'upload_conversation_link')
        set_user_attr(msg.chat.id, 'topic', '')
    if current_state == 'upload_conversation_link':
        bot.send_message(msg.chat.id,
                         'Отправьте квадратную фотографию или нажмите /skip, чтобы пропустить этот шаг. Она будет видна клиенту вместе с названием и описанием.')
        set_state(msg.chat.id, 'upload_logo')
        set_user_attr(msg.chat.id, 'chat_url', '')
    if current_state == 'upload_logo':
        save_course(msg.chat.id)


@bot.message_handler(state='enter_title')
def enter_title(msg):
    """
    Хэндлер ввода названия создающегося курса
    :param msg: Входящее сообщение
    """
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
    """
    Хэндлер ввода описания создающегося курса
    :param msg: Входящее сообщение
    """
    action = get_user_attr(msg.chat.id, 'action')
    if action != 'change_description':
        bot.send_message(msg.chat.id,
                         'Введите цену вашего курса в рублях (больше 1 рубля) или нажмите /free, чтобы сделать его бесплатным')
        set_state(msg.chat.id, 'enter_price')
        set_user_attr(msg.chat.id, 'description', msg.text)
    else:
        bot.send_message(msg.chat.id, 'Описание успешно изменено')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'description': msg.text})


@bot.message_handler(commands=['free'])
@bot.message_handler(state='enter_price', func=lambda msg: check_price(msg.text))
def enter_correct_price(msg):
    """
    Хэндлер ввода цены создающегося курса
    :param msg: Входящее сообщение
    """
    price = 0 if msg.text == '/free' else msg.text
    action = get_user_attr(msg.chat.id, 'action')
    if action != 'change_price':
        bot.send_message(msg.chat.id,
                         'Выберите сферу, по которой вы собираетесь сделать ваш курс или нажмите /skip, чтобы пропустить этот шаг. (Если вы хотите добавить ещё какую-то сферу жизни в этот список, напишите об этом в отзыве)',
                         reply_markup=topics_table)
        set_state(msg.chat.id, 'choose_topic')
        set_user_attr(msg.chat.id, 'price', price)
    else:
        bot.send_message(msg.chat.id, 'Цена успешно изменена')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'price': price})


@bot.message_handler(state='enter_price', func=lambda msg: not check_price(msg.text))
def enter_incorrect_price(msg):
    """
    Хэндлер обработки некорректного ввода цены создающегося курса
    :param msg: Входящее сообщение
    """
    bot.send_message(msg.chat.id, 'Некорректная цена. Введите пожалуйста целое число >= 2')


@bot.callback_query_handler(state='choose_topic', func=lambda call: 'topic' in call.data)
def choose_topic(call):
    """
    Хэндлер выбора сферы создающегося курса
    :param call: Входящий callback запрос
    """
    action = get_user_attr(call.message.chat.id, 'action')
    chosen_topic_id = int(call.data.split('_')[-1])
    topic = Topics.get_by_id(chosen_topic_id)

    if action != 'change_topic':
        bot.edit_message_text(f'Вы выбрали тему "{topic.text}"', call.message.chat.id, message_id=call.message.id,
                              reply_markup=None)
        set_user_attr(call.message.chat.id, 'topic', chosen_topic_id)
        bot.send_message(call.message.chat.id,
                         'Создайте группу в Telegram, и пришлите ссылку на неё или пока пропустите этот шаг, нажав /skip. Все клиенты Вашего курса смогут в неё войти и обсуждать интересные темы.')
        set_state(call.message.chat.id, 'upload_conversation_link')
    else:
        bot.edit_message_text('Сфера успешно изменена', chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=None)
        delete_state(call.message.chat.id)
        Course.set_by_id(get_user_attr(call.message.chat.id, 'current_course'), {'topic_id': chosen_topic_id})


@bot.message_handler(state='upload_conversation_link')
def upload_conversation_link(msg):
    """
    Хэндлер ввода ссылки на обсуждение клиентов создающегося курса
    :param msg: Входящее сообщение
    """
    action = get_user_attr(msg.chat.id, 'action')

    if action != 'change_link':
        bot.send_message(msg.chat.id,
                         'Отправьте квадратную фотографию или нажмите /skip, чтобы пропустить этот шаг. Она будет видна клиенту вместе с названием и описанием.')
        set_state(msg.chat.id, 'upload_logo')
        set_user_attr(msg.chat.id, 'chat_url', msg.text)
    else:
        bot.send_message(msg.chat.id, 'Ссылка на обсуждение успешно изменена')
        delete_state(msg.chat.id)
        Course.set_by_id(get_user_attr(msg.chat.id, 'current_course'), {'chat_url': msg.text})


@bot.message_handler(state='upload_logo', content_types=['photo'])
def upload_logo(msg: Message):
    """
    Хэндлер загрузки фотки/логотипа создающегося курса
    :param msg: Входящее сообщение
    """
    file_id = msg.photo[-1].file_id
    if is_image_square(file_id):
        save_course(msg.chat.id, file_id)
    else:
        logo = crop_photo_to_square(file_id)
        bot.send_message(msg.chat.id, 'Устраивает ли Вас такая фотография?')
        bot.send_photo(msg.chat.id, logo, reply_markup=yes_no_table)
    set_user_attr(msg.chat.id, 'file_id', file_id)


@bot.callback_query_handler(state='upload_logo', func=lambda call: 'choice' in call.data)
def logo_confirmation(call):
    """
    Хэндлер подтвержения, что обрезанная до квадрата фотка/логотип пользователя устраивает
    :param msg: Входящее сообщение
    """
    if 'yes' in call.data:
        save_course(call.message.chat.id, get_user_attr(call.message.chat.id, 'file_id'))
    else:
        bot.send_message(call.message.chat.id,
                         'Загрузите новую фотографию или нажмите /skip, чтобы пропустить этот шаг.')
