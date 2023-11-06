import io
import json
import locale
import re
from typing import Dict

import requests
from PIL import Image
from dotenv import dotenv_values
from telebot import SimpleCustomFilter

from App_creators import tables
from App_creators.config import bot, s3
from database.models import Users, Course

values = dotenv_values()


class StateFilter(SimpleCustomFilter):
    """
    Фильтр, проверяющий статус пользователя
    """
    key = 'state'

    def check(self, obj):
        if not hasattr(obj, 'chat'):
            obj = obj.message
        return get_user_attr(obj.chat.id, 'state')


class EditingCourseFilter(SimpleCustomFilter):
    """
    Фильтр, проверяющий действительно ли пользователь в данный момент в меню редактирирования курса
    """
    key = 'is_edit_course'

    def check(self, obj):
        if not hasattr(obj, 'chat'):
            obj = obj.message
        return get_user_attr(obj.chat.id, 'current_course') != ''


def check_price(text):
    """
    :param text: Произвольный текст
    :return: Является ли строка целым чиcлом больше 1 или free
    """
    if text == 'free':
        return True
    if isinstance(text, int):
        return text >= 2
    if not isinstance(text, str):
        raise TypeError
    return text.isdigit() and int(text) >= 2


def check_bank_card(text):
    """
    Проверка строки на номер карты
    :param text: Произвольный текст
    """
    if isinstance(text, int):
        return len(str(text)) >= 16
    if not isinstance(text, str):
        raise TypeError

    return text.isdigit() and 16 <= len(text)


def set_user_attr(chat_id, attr, data):
    """
    Позволяет записать любую информацию о пользователе по ключу
    :param chat_id: Chat_id пользователя
    :param attr: Ключ, по которому в базе будет хранится информация
    :param data: Сама важная информация
    """
    attrs_str = Users.get(Users.chat_id == chat_id).attrs
    attrs_dict = json.loads(attrs_str)
    attrs_dict[attr] = data
    query = Users.update({Users.attrs: json.dumps(attrs_dict)}).where(Users.chat_id == chat_id)
    query.execute()


def set_state(chat_id, state):
    """
    Позволяет установить статус пользователя
    :param chat_id: Chat_id пользователя
    :param state: Статус пользователя, который хотим установить
    """
    set_user_attr(chat_id, 'state', state)


def delete_state(chat_id):
    """
    Позволяет удалить статус пользователя
    :param chat_id: Chat_id пользователя
    """
    set_user_attr(chat_id, 'state', '')


def get_state(chat_id):
    """
    Позволяет получить статус пользователя
    :param chat_id: Chat_id пользователя
    """
    return get_user_attr(chat_id, 'state')


def get_user_attrs(chat_id) -> Dict:
    """
    Позволяет получить словарь со всеми данными о пользователе
    :param chat_id: Chat_id пользователя
    """
    return json.loads(Users.get(Users.chat_id == chat_id).attrs)


def get_user_attr(chat_id, attr):
    """
    Позволяет получить информацию о пользователе по ключу
    :param chat_id: Chat_id пользователя
    :param attr: Ключ
    """
    try:
        state_json = json.loads(Users.get(Users.chat_id == chat_id).attrs)
        if attr in state_json.keys():
            return state_json[attr]
    except:
        return ''


def is_image_square(file_id):
    """
    :param file_id: Id картинки у Telegram
    :return: Квадратное ли изображение?
    """
    image = get_image_from_file_id(file_id)
    return image.width == image.height


def crop_photo_to_square(file_id):
    """
    :param file_id: Id картинки у Telegram
    :return: Обрезанное до квадрата изображение
    """
    image = get_image_from_file_id(file_id)
    delta = (image.width - image.height) // 2
    if delta <= 0:
        cropped_image = image.crop((0, -delta, image.width, image.height + delta))
    elif delta > 0:
        cropped_image = image.crop((delta, 0, image.width - delta, image.height))

    return cropped_image


def get_image_from_file_id(file_id):
    """
    :param file_id: Id картинки у Telegram
    :return: Изображение в виде объекта класса Image
    """
    resp = requests.get(
        bot.get_file_url(file_id),
        stream=True)
    return Image.open(resp.raw)


def save_course(chat_id, file_id=''):
    """
    Сохраняет курс по введённым данным
    :param chat_id: Chat_id пользователя
    :param file_id: Id картинки у Telegram
    """
    try:
        user_id = Users.select().where(Users.chat_id == chat_id)[0].id
    except:
        bot.send_message(chat_id, 'Вас нет в базе пользователей, нажмите /start, и попробуйте снова')
        return

    action = get_user_attr(chat_id, 'action')
    current_course_id = get_user_attr(chat_id, 'current_course')
    if not action or 'change_logo' not in action:
        user_attrs = get_user_attrs(chat_id)
        topic = user_attrs['topic']
        if topic == '':
            new_course = Course.create(
                user_id=user_id,
                title=user_attrs['title'],
                description=user_attrs['description'],
                price=user_attrs['price'],
                have_logo=bool(file_id),
                chat_url=user_attrs['chat_url']
            )
        else:
            new_course = Course.create(
                user_id=user_id,
                title=user_attrs['title'],
                description=user_attrs['description'],
                price=user_attrs['price'],
                have_logo=bool(file_id),
                topic_id=topic,
                chat_url=user_attrs['chat_url']
            )

        set_user_attr(chat_id, 'current_course', int(new_course.get_id()))
        current_course_id = new_course.get_id()
        bot.send_message(chat_id, 'Курс создан, теперь Вы можете добавлять новые темы',
                         reply_markup=tables.get_edit_course_table(chat_id))
    else:
        bot.send_message(chat_id, 'Фотография успешно изменена',
                         reply_markup=tables.get_edit_course_table(chat_id))

    delete_state(chat_id)

    if file_id != '':
        logo = crop_photo_to_square(file_id)
        stream = io.BytesIO()
        logo.save(stream, 'JPEG')
        stream.seek(0)
        s3.upload_fileobj(stream, 'mybacket', f'logos/{current_course_id}.jpg')


def get_image_from_s3(backet, path):
    """
    :param backet: Бакет
    :param path: Путь к файлу
    :return: Изображение из удалённой s3 базы в виде объекта класса Image
    """
    obj = s3.get_object(Bucket=backet, Key=path)
    return Image.open(obj['Body'])


def get_current_order_of_lessons(chat_id, for_creator=True):
    """
    :param chat_id: Chat_id пользователя
    :param for_creator: Для создателя курса другой атрибут
    :return: Порядок уроков у редактируемого курса
    """
    if for_creator:
        key = 'current_course'
    else:
        key = 'current_course_main'
    return Course.get_by_id(get_user_attr(chat_id, key)).order_of_lessons


def check_slang(string):
    """
    Функция проверки на нецензурную лексику
    :param string: Любой текст
    """
    oldloc = locale.getlocale(locale.LC_CTYPE)
    locale.setlocale(locale.LC_CTYPE, 'ru_RU.CP1251')
    expr = r'a[\W_]*s[\W_]*s(?:[\W_]*e[\W_]*s)?|f[\W_]*u[\W_]*c[\W_]*k(?:[\W_]*i[\W_]*n[\W_]*g)?|ж[\W_]*(?:[ыиiu][\W_]*[дd](?:[\W_]*[уыаyiau]|[\W_]*[оo0][\W_]*[вbv])?|[оo0][\W_]*[пnp][\W_]*(?:[аa](?:[\W_]*[хxh])?|[уеыeyiu]|[оo0][\W_]*[йj]))|[дd][\W_]*[еe][\W_]*[рpr][\W_]*(?:[ьb][\W_]*)?[мm][\W_]*[оуеаeoya0u](?:[\W_]*[мm])?|[чc][\W_]*[мm][\W_]*(?:[оo0]|[ыi][\W_]*[рpr][\W_]*[еиьяeibu])|[сsc][\W_]*[уuy][\W_]*(?:(?:[чc][\W_]*)?[кk][\W_]*[ауиiyau](?:[\W_]*[нhn](?:[\W_]*[оo0][\W_]*[йj]|[\W_]*[уаыyiau])?)?|[чc][\W_]*(?:(?:[ьb][\W_]*)?(?:[еёяиeiu]|[еиeiu][\W_]*[йj])|[аa][\W_]*[рpr][\W_]*[ыауеeyiau]))|[гrg][\W_]*(?:[аоoa0][\W_]*(?:[нhn][\W_]*[дd][\W_]*[аоoa0][\W_]*[нhn](?:[\W_]*[ыуyiu])?|[вbv][\W_]*[нhn][\W_]*[оаoa0](?:[\W_]*(?:[мm]|[еe][\W_]*[дd](?:[\W_]*[ыуаеeyiau]|[\W_]*[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?)?))?)|[нhn][\W_]*(?:[иiu][\W_]*[дd][\W_]*(?:[ыуеаeyiau]|[оo0][\W_]*[йj])|[уyu][сsc](?:[\W_]*[аыуyiau]|[\W_]*[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?)?))|(?:[нhn][\W_]*[еe][\W_]*)?(?:(?:[з3z][\W_]*[аa]|[оo0][тt]|[пnp][\W_]*[оo0]|[пnp][\W_]*(?:[еe][\W_]*[рpr][\W_]*[еe]|[рpr][\W_]*[оеиeiou0]|[иiu][\W_]*[з3z][\W_]*[дd][\W_]*[оo0])|[нhn][\W_]*[аa]|[иiu][\W_]*[з3z]|[дd][\W_]*[оo0]|[вbv][\W_]*[ыi]|[уyu]|[рpr][\W_]*[аa][\W_]*[з3z]|[з3z][\W_]*[лl][\W_]*[оo0]|[тt][\W_]*[рpr][\W_]*[оo0]|[уyu])[\W_]*)?(?:[вbv][\W_]*[ыi][\W_]*)?(?:[ъьb][\W_]*)?(?:[еёe][\W_]*[бb6](?:(?:[\W_]*[оеёаиуeioyau0])?(?:[\W_]*[нhn](?:[\W_]*[нhn])?[\W_]*[яуаиьiybau]?)?(?:[\W_]*[вbv][\W_]*[аa])?(?:(?:[\W_]*(?:[иеeiu]ш[\W_]*[ьb][\W_]*[сsc][\W_]*я|[тt][\W_]*(?:(?:[ьb][\W_]*)?[сsc][\W_]*я|[ьb]|[еe][\W_]*[сsc][\W_]*[ьb]|[еe]|[оo0]|[иiu][\W_]*[нhn][\W_]*[уыеаeyiau])|(?:щ[\W_]*(?:[иiu][\W_]*[йj]|[аa][\W_]*я|[иеeiu][\W_]*[еe]|[еe][\W_]*[гrg][\W_]*[оo0])|ю[\W_]*[тt])(?:[\W_]*[сsc][\W_]*я)?|[еe][\W_]*[мтmt]|[кk](?:[\W_]*[иаiau])?|[аa][\W_]*[лl](?:[\W_]*[сsc][\W_]*я)?|[лl][\W_]*(?:[аa][\W_]*[нhn]|[оаoa0](?:[\W_]*[мm])?|(?:[иiu][\W_]*)?[сsc][\W_]*[ьяb]|[иiu]|[аa][\W_]*[сsc][\W_]*[ьb])|[рpr][\W_]*[ьb]|[сsc][\W_]*[яьb]|[нhn][\W_]*[оo0]|[чc][\W_]*(?:[иiu][\W_]*[хxh]|[еe][\W_]*[сsc][\W_]*[тt][\W_]*[ьиibu](?:[\W_]*ю)?)|(?:[тt][\W_]*[еe][\W_]*[лl][\W_]*[ьb][\W_]*[сsc][\W_]*[кk][\W_]*|[сsc][\W_]*[тt][\W_]*|[лl][\W_]*[иiu][\W_]*[вbv][\W_]*|[чтtc][\W_]*)?(?:[аa][\W_]*я|[оo0][\W_]*[йемejm]|[ыi][\W_]*[хйеejxh]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[иiu][\W_]*[еe]|[оo0][\W_]*[мm][\W_]*[уyu]|[иiu][\W_]*[йj]|[еe][\W_]*[вbv]|[иiu][\W_]*[мm](?:[\W_]*[иiu])?)|[чтыйилijltcu]))?)|[\W_]*[ыi](?:(?:[\W_]*[вbv][\W_]*[аa]|[\W_]*[нhn](?:[\W_]*[нhn])?)(?:(?:[\W_]*(?:[иеeiu]ш[\W_]*[ьb][\W_]*[сsc][\W_]*я|[тt][\W_]*(?:[ьb][\W_]*[сsc][\W_]*я|[ьb]|[еe][\W_]*[сsc][\W_]*[ьb]|[еe]|[иiu][\W_]*[нhn][\W_]*[уыеаeyiau])|(?:щ[\W_]*(?:[иiu][\W_]*[йj]|[аa][\W_]*я|[иеeiu][\W_]*[еe]|[еe][\W_]*[гrg][\W_]*[оo0])|ю[\W_]*[тt])(?:[\W_]*[сsc][\W_]*я)?|[еe][\W_]*[мтmt]|[лl][\W_]*(?:(?:[иiu][\W_]*)?[сsc][\W_]*[ьяb]|[иiu]|[аa][\W_]*[сsc][\W_]*[ьb])|(?:[сsc][\W_]*[тt][\W_]*|[лl][\W_]*[иiu][\W_]*[вbv][\W_]*|[чтtc][\W_]*)?(?:[аa][\W_]*я|[оo0][\W_]*[йемejm]|[ыi][\W_]*[хйеejxh]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[иiu][\W_]*[еe]|[оo0][\W_]*[мm][\W_]*[уyu]|[иiu][\W_]*[йj]|[еe][\W_]*[вbv]|[иiu][\W_]*[мm](?:[\W_]*[иiu])?))))|[рpr][\W_]*[ьb]))|я[\W_]*[бb6](?:[\W_]*[оеёаиуeioyau0])?(?:(?:[\W_]*[нhn](?:[\W_]*[нhn])?[\W_]*[яуаиьiybau]?)?(?:(?:[\W_]*(?:[иеeiu]ш[\W_]*[ьb][\W_]*[сsc][\W_]*я|[тt][\W_]*(?:[ьb][\W_]*[сsc][\W_]*я|[ьb]|[еe][\W_]*[сsc][\W_]*[ьb]|[еe]|[иiu][\W_]*[нhn][\W_]*[уыеаeyiau])|(?:щ[\W_]*(?:[иiu][\W_]*[йj]|[аa][\W_]*я|[иеeiu][\W_]*[еe]|[еe][\W_]*[гrg][\W_]*[оo0])|ю[\W_]*[тt])(?:[\W_]*[сsc][\W_]*я)?|[еe][\W_]*[мтmt]|[кk](?:[\W_]*[иаiau])?|[аa][\W_]*[лl](?:[\W_]*[сsc][\W_]*я)?|[лl][\W_]*(?:[аa][\W_]*[нhn]|[оаoa0](?:[\W_]*[мm])?|(?:[иiu][\W_]*)?[сsc][\W_]*[ьяb]|[иiu])|[рpr][\W_]*[ьb]|[сsc][\W_]*[яьb]|[нhn][\W_]*[оo0]|[чc][\W_]*(?:[иiu][\W_]*[хxh]|[еe][\W_]*[сsc][\W_]*[тt][\W_]*[ьиibu](?:[\W_]*ю)?)|(?:[тt][\W_]*[еe][\W_]*[лl][\W_]*[ьb][\W_]*[сsc][\W_]*[кk][\W_]*|[сsc][\W_]*[тt][\W_]*|[лl][\W_]*[иiu][\W_]*[вbv][\W_]*|[чтtc][\W_]*)?(?:[аa][\W_]*я|[оo0][\W_]*[йемejm]|[ыi][\W_]*[хйеejxh]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[иiu][\W_]*[еe]|[оo0][\W_]*[мm][\W_]*[уyu]|[иiu][\W_]*[йj]|[еe][\W_]*[вbv]|[иiu][\W_]*[мm](?:[\W_]*[иiu])?)|[чмйилijlmcu]))|(?:[\W_]*[нhn](?:[\W_]*[нhn])?[\W_]*[яуаиьiybau]?)))|я[\W_]*[бb6][\W_]*(?:[еёаиуeiyau][\W_]*)?(?:[нhn][\W_]*(?:[нhn][\W_]*)?(?:[яуаиьiybau][\W_]*)?)?[тt])|[сsc][\W_]*[ьъb][\W_]*[еяёe][\W_]*[бb6][\W_]*(?:[уyu]|(?:[еиёауeiyau](?:[\W_]*[лl](?:[\W_]*[иоаioau0])?|[\W_]*ш[\W_]*[ьb]|[\W_]*[тt][\W_]*[еe])?(?:[\W_]*[сsc][\W_]*[ьяb])?))|[еe][\W_]*(?:[бb6][\W_]*(?:[уyu][\W_]*[кk][\W_]*[еe][\W_]*[нhn][\W_]*[тt][\W_]*[иiu][\W_]*[йj]|[еe][\W_]*[нhn][\W_]*(?:[ьb]|я(?:[\W_]*[мm])?)|[иiu][\W_]*(?:[цc][\W_]*[кk][\W_]*[аa][\W_]*я|[чc][\W_]*[еe][\W_]*[сsc][\W_]*[кk][\W_]*[аa][\W_]*я)|[лl][\W_]*[иiu][\W_]*щ[\W_]*[еe]|[аa][\W_]*(?:[лl][\W_]*[ьb][\W_]*[нhn][\W_]*[иiu][\W_]*[кk](?:[\W_]*[иаiau])?|[тt][\W_]*[оo0][\W_]*[рpr][\W_]*[иiu][\W_]*[йj]|[нhn][\W_]*(?:[тt][\W_]*[рpr][\W_]*[оo0][\W_]*[пnp]|[аa][\W_]*[тt][\W_]*[иiu][\W_]*(?:[кk]|[чc][\W_]*[еe][\W_]*[сsc][\W_]*[кk][\W_]*[иiu][\W_]*[йj]))))|[дd][\W_]*[рpr][\W_]*[иiu][\W_]*[тt])|[нhn][\W_]*[еe][\W_]*[вbv][\W_]*[рpr][\W_]*[оo0][\W_]*[тt][\W_]*ъ[\W_]*[еe][\W_]*[бb6][\W_]*[аa][\W_]*[тt][\W_]*[еe][\W_]*[лl][\W_]*[ьb][\W_]*[сsc][\W_]*[кk][\W_]*[иiu][\W_]*(?:[ыиiu][\W_]*[йj]|[аa][\W_]*я|[оo0][\W_]*[ейej]|[ыi][\W_]*[хxh]|[ыi][\W_]*[еe]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu])|[уyu][\W_]*(?:[ёеe][\W_]*[бb6][\W_]*(?:[иiu][\W_]*щ[\W_]*[еаea]|[аa][\W_]*[нhn](?:[\W_]*[тt][\W_]*[уyu][\W_]*[сsc])?(?:[\W_]*[аоoa0][\W_]*[вмbmv]|[\W_]*[ыуеаeyiau])?)|[рpr][\W_]*[оo0][\W_]*[дd](?:[\W_]*[аоoa0][\W_]*[вмbmv]|[\W_]*[ыуеаeyiau])?|[бb6][\W_]*[лl][\W_]*ю[\W_]*[дd][\W_]*(?:[оo0][\W_]*[кk]|[кk][\W_]*(?:[аоoa0][\W_]*[вмbmv](?:[\W_]*[иiu])?|[иуеаeiyau])?))|[мm][\W_]*(?:[уyu][\W_]*[дd][\W_]*(?:[оo0][\W_]*[хxh][\W_]*[аa][\W_]*(?:[тt][\W_]*[ьb][\W_]*[сsc][\W_]*я|ю[\W_]*[сsc][\W_]*[ьb]|[еe][\W_]*ш[\W_]*[ьb][\W_]*[сsc][\W_]*я)|[аa][\W_]*(?:[кk](?:[\W_]*[иаiau]|[оo0][мвbmv])?|[чc][\W_]*(?:[ьb][\W_]*[еёe]|[иiu][\W_]*[нhn][\W_]*[уыаyiau]|[кk][\W_]*(?:[аиеуeiyau]|[оo0][\W_]*[йj])))|[еe][\W_]*[нhn][\W_]*[ьb]|[иiu][\W_]*[лl](?:[\W_]*[аеоыeoia0]?))|[аa][\W_]*[нhn][\W_]*[дd][\W_]*[уаyau]|[лl][\W_]*(?:[иiu][\W_]*[нhn]|я))|(?:[мm][\W_]*(?:[оo0][\W_]*[з3z][\W_]*[гrg]|[уyu][\W_]*[дd])|[дd][\W_]*(?:[оo0][\W_]*[лl][\W_]*[бb6]|[уyu][\W_]*[рpr])|[сsc][\W_]*[кk][\W_]*[оo0][\W_]*[тt]|ж[\W_]*[иiu][\W_]*[дd])[\W_]*[аоoa0][\W_]*(?:[хxh][\W_]*[уyu][\W_]*[ийяiju]|[ёеe][\W_]*[бb6](?:[\W_]*[еоeo0][\W_]*[вbv]|[\W_]*[ыаia]|[\W_]*[сsc][\W_]*[тt][\W_]*[вbv][\W_]*[оуoy0u](?:[\W_]*[мm])?|[иiu][\W_]*[з3z][\W_]*[мm])?)|(?:[нhn][\W_]*[еe][\W_]*|[з3z][\W_]*[аa][\W_]*|[оo0][\W_]*[тt][\W_]*|[пnp][\W_]*[оo0][\W_]*|[нhn][\W_]*[аa][\W_]*|[рpr][\W_]*[аa][\W_]*[сз3szc][\W_]*)?(?:[пnp][\W_]*[иiu][\W_]*[з3z][\W_]*[дd][\W_]*[ияеeiu]|(?:ъ)?[еёe][\W_]*[бb6][\W_]*[аa])[\W_]*(?:(?:[тt][\W_]*[ьb][\W_]*[сsc][\W_]*я|[тt][\W_]*[ьb]|[лl][\W_]*[иiu]|[аa][\W_]*[лl]|[лl]|c[\W_]*[ьb]|[иiu][\W_]*[тt]|[иiu]|[тt][\W_]*[еe]|[чc][\W_]*[уyu]|ш[\W_]*[ьb])|(?:[йяиiju]|[иеeiu][\W_]*[мm](?:[\W_]*[иiu])?|[йj][\W_]*[сsc][\W_]*(?:[кk][\W_]*(?:[ыиiu][\W_]*[йеej]|[аa][\W_]*я|[оo0][\W_]*[еe]|[ыi][\W_]*[хxh]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu])|[тt][\W_]*[вbv][\W_]*[оуаoya0u](?:[\W_]*[мm])?)))|[пnp][\W_]*[еиыeiu][\W_]*[дd][\W_]*[аеэоeoa0][\W_]*[рpr](?:(?:[\W_]*[аa][\W_]*[сз3szc](?:(?:[\W_]*[тt])?(?:[\W_]*[ыi]|[\W_]*[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?|[\W_]*[кk][\W_]*[аиiau])?|(?:[\W_]*[ыуаеeyiau]|[\W_]*[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?|[\W_]*[оo0][\W_]*[вbv])))|[\W_]*(?:[ыуаеeyiau]|[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?|[оo0][\W_]*[вbv]|[нhn][\W_]*я))?|[пnp][\W_]*[иiu][\W_]*[з3z][\W_]*(?:[ьb][\W_]*)?[дd][\W_]*(?:[ёеe][\W_]*(?:[нhn][\W_]*[ыi][\W_]*ш(?:[\W_]*[ьb])?|[шнжhn](?:[\W_]*[ьb])?)|[уyu][\W_]*(?:[йj](?:[\W_]*[тt][\W_]*[еe])?|[нhn](?:[\W_]*[ыi])?)|ю[\W_]*(?:[кk](?:[\W_]*(?:[аеуиeiyau]|[оo0][\W_]*[вbv]|[аa][\W_]*[мm](?:[\W_]*[иiu])?))?|[лl](?:[ьиibu]|[еe][\W_]*[йj]|я[\W_]*[хмmxh]))|[еe][\W_]*[цc]|[аоoa0][\W_]*(?:[нhn][\W_]*[уyu][\W_]*)?[тt][\W_]*(?:[иiu][\W_]*[йj]|[аa][\W_]*я|[оo0](?:[\W_]*[ейej])?|[ыi][\W_]*[ейхejxh]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu]|[еe][\W_]*[еe]|[ауьеыeyibau])|[аa][\W_]*[нhn][\W_]*[уyu][\W_]*[лl](?:[\W_]*[аиiau])?|[ыеуиаeiyau]|[оаoa0][\W_]*(?:[йj]|[хxh][\W_]*[уyu][\W_]*[йj]|[еёe][\W_]*[бb6]|(?:[рpr][\W_]*[оo0][\W_]*[тt]|[гrg][\W_]*[оo0][\W_]*[лl][\W_]*[оo0][\W_]*[вbv])[\W_]*(?:[ыиiu][\W_]*[йj]|[аa][\W_]*я|[оo0][\W_]*[ейej]|[ыi][\W_]*[хxh]|[ыi][\W_]*[еe]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu])|[бb6][\W_]*(?:[рpr][\W_]*[аa][\W_]*[тt][\W_]*[иiu][\W_]*я|[оo0][\W_]*[лl](?:[\W_]*[аыуyiau])?)))|[пnp][\W_]*(?:[аa][\W_]*[дd][\W_]*[лl][\W_]*[аоыoia0]|[оаoa0][\W_]*[сsc][\W_]*[кk][\W_]*[уyu][\W_]*[дd][\W_]*(?:[ыуаеeyiau]|[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?)|[иеeiu][\W_]*[дd][\W_]*(?:[иiu][\W_]*[кk]|[рpr][\W_]*[иiu][\W_]*[лl](?:[\W_]*[лl])?)(?:[\W_]*[оаoa0][\W_]*[мвbmv]|[\W_]*[иуеоыаeioyau0])?|[рpr][\W_]*[оo0][\W_]*[бb6][\W_]*[лl][\W_]*я[\W_]*[дd][\W_]*[оo0][\W_]*[мm])|(?:[з3z][\W_]*[аa][\W_]*|[оo0][\W_]*[тt][\W_]*|[нhn][\W_]*[аa][\W_]*)?[сsc][\W_]*[рpr][\W_]*(?:[аa][\W_]*[тt][\W_]*[ьb]|[аa][\W_]*[лl](?:[\W_]*[иiu])?|[eуиiyu])|[сsc][\W_]*[рpr][\W_]*[аa][\W_]*(?:[кk][\W_]*(?:[аеиуeiyau]|[оo0][\W_]*[йj])|[нhn](?:[\W_]*[нhn])?(?:[ьb]|(?:[\W_]*[ыi][\W_]*[йеej]|[\W_]*[аa][\W_]*я|[\W_]*[оo0][\W_]*[еe]))|[лl][\W_]*[ьb][\W_]*[нhn][\W_]*[иiu][\W_]*[кk](?:[\W_]*[иiu]|[\W_]*[оаoa0][\W_]*[мm])?)|(?:[з3z][\W_]*[аa][\W_]*)?[тt][\W_]*[рpr][\W_]*[аa][\W_]*[хxh][\W_]*(?:[нhn][\W_]*(?:[уyu](?:[\W_]*[тt][\W_]*[ьb](?:[\W_]*[сsc][\W_]*я)?|[\W_]*[сsc][\W_]*[ьb]|[\W_]*[лl](?:[\W_]*[аиiau])?)?|[еиeiu][\W_]*ш[\W_]*[ьb][\W_]*[сsc][\W_]*я)|[аa][\W_]*(?:[лl](?:[\W_]*[аоиioau0])?|[тt][\W_]*[ьb](?:[\W_]*[сsc][\W_]*я)?|[нhn][\W_]*(?:[нhn][\W_]*)?(?:[ыиiu][\W_]*[йj]|[аa][\W_]*я|[оo0][\W_]*[йеej]|[ыi][\W_]*[хxh]|[ыi][\W_]*[еe]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu])))|(?:[нhn][\W_]*[иеeiu][\W_]*|[пnp][\W_]*[оo0][\W_]*|[нhn][\W_]*[аa][\W_]*|[оаoa0][\W_]*(?:[тt][\W_]*)?|[дd][\W_]*[аоoa0][\W_]*|[з3z][\W_]*[аa][\W_]*)?(?:(?:[фf][\W_]*[иiu][\W_]*[гrg]|[хxh][\W_]*(?:[еиeiu][\W_]*(?:[йj][\W_]*)?[рpr]|[рpr][\W_]*[еe][\W_]*[нhn]|[уyu](?:[\W_]*[йj])?))(?:[\W_]*[еоёeo0][\W_]*[вbv](?:[\W_]*[аa][\W_]*ю[\W_]*щ|[\W_]*ш)?)?(?:[\W_]*[аиеeiau][\W_]*[лнlhn])?(?:[нhn])?(?:[\W_]*(?:[иаоёяыеeioau0][юяиевмйbeijmvu]|я[\W_]*(?:[мm](?:[\W_]*[иiu])?|[рpr][\W_]*(?:ю|[иiu][\W_]*(?:[тt](?:[\W_]*[ьеeb][\W_]*[сsc][\W_]*[яьb])?|[лl](?:[\W_]*[иоаioau0])?))|[чc][\W_]*(?:[аиiau][\W_]*[тt](?:[\W_]*[сsc][\W_]*я)|[иiu][\W_]*[лl](?:[\W_]*[иоаioau0])?)|[чc](?:[\W_]*[ьb])?)|[еe][\W_]*(?:[тt][\W_]*(?:[оo0][\W_]*[йj]|[аьуybau])|[еe][\W_]*(?:[тt][\W_]*[еe]|ш[\W_]*[ьb]))|[аыоуяюйиijoyau0]|[лl][\W_]*[иоiou0]|[чc][\W_]*[уyu])))|(?:[фf][\W_]*[иiu][\W_]*[гrg]|[хxh][\W_]*(?:[еиeiu][\W_]*(?:[йj][\W_]*)?[рpr]|[рpr][\W_]*[еe][\W_]*[нhn]|[уyu][\W_]*[йj]))|[хxh][\W_]*[уyu][\W_]*(?:[еёиeiu][\W_]*(?:[сsc][\W_]*[оo0][\W_]*[сsc]|[пnp][\W_]*[лl][\W_]*[еe][\W_]*[тt]|[нhn][\W_]*[ыi][\W_]*ш)(?:[\W_]*[аыуyiau]|[\W_]*[оаoa0][\W_]*[мm](?:[\W_]*[иiu])?|[нhn][\W_]*(?:[ыиiu][\W_]*[йj]|[аa][\W_]*я|[оo0][\W_]*[йеej]|[ыi][\W_]*[хxh]|[ыi][\W_]*[еe]|[ыi][\W_]*[мm](?:[\W_]*[иiu])?|[уyu][\W_]*ю|[оo0][\W_]*[мm][\W_]*[уyu]))?|[дd][\W_]*[оo0][\W_]*ё[\W_]*[бb6][\W_]*[иiu][\W_]*[нhn][\W_]*(?:[оo0][\W_]*[йj]|[аеыуeyiau]))|[бb6][\W_]*[лl][\W_]*я(?:[\W_]*[дтdt][\W_]*(?:[ьb]|[иiu]|[кk][\W_]*[иiu]|[сsc][\W_]*[тt][\W_]*[вbv][\W_]*[оo0]|[сsc][\W_]*[кk][\W_]*(?:[оo0][\W_]*[ейej]|[иiu][\W_]*[еe]|[аa][\W_]*я|[иiu][\W_]*[йj]|[оo0][\W_]*[гrg][\W_]*[оo0])))?|[вbv][\W_]*[ыi][\W_]*[бb6][\W_]*[лl][\W_]*я[\W_]*[дd][\W_]*(?:[оo0][\W_]*[кk]|[кk][\W_]*(?:[иуаеeiyau]|[аa][\W_]*[мm](?:[\W_]*[иiu])?))|(?:[з3z][\W_]*[аоoa0][\W_]*)(?:[пnp][\W_]*[аоoa0][\W_]*[дd][\W_]*[лl][\W_]*[оыаoia0]|[лl][\W_]*[уyu][\W_]*[пnp][\W_]*(?:[оo0][\W_]*[йj]|[аеыуeyiau]))|ш[\W_]*[лl][\W_]*ю[\W_]*[хxh][\W_]*(?:[ауеиeiyau]|[оo0][\W_]*[йj])|[аa][\W_]*[нhn][\W_]*[уyu][\W_]*[сsc](?:[\W_]*[еаыуeyiau]|[\W_]*[оo0][\W_]*[мm])?|(?:\w*(?:[хxh](?:[рpr][еe][нhn]|[уyu][иiu])|[пnp][еиeiu](?:[з3z][дd]|[дd](?:[еаоeoa0][рpr]|[рpr]))|[бb6][лl]я[дd]|[оo0][хxh][уyu][еe]|[мm][уyu][дd][еоиаeioau0]|[дd][еe][рpr][ьb]|[гrg][аоoa0][вbv][нhn]|[уyu][еёe][бb6])|[хxh][\W_]*(?:[рpr][\W_]*[еe][\W_]*[нhn]|[уyu][\W_]*[йиеяeiju])|[пnp][\W_]*[еиeiu][\W_]*(?:[з3z][\W_]*[дd]|[дd][\W_]*(?:[еаоeoa0][\W_]*[рpr]|[рpr]))|[бb6][\W_]*[лl][\W_]*я[\W_]*[дd]|[оo0][\W_]*[хxh][\W_]*[уyu][\W_]*[еe]|[мm][\W_]*[уyu][\W_]*[дd][\W_]*[еоиаeioau0]|[дd][\W_]*[еe][\W_]*[рpr][\W_]*[ьb]|[гrg][\W_]*[аоoa0][\W_]*[вbv][\W_]*[нhn]|[уyu][\W_]*[еёe][\W_]*[бb6]|[ёеe][бb6])\w+';
    expr = r'(?:\b|(?<=_))(?:' + expr + r')(?:\b|(?=_))'
    expr = expr.encode('windows-1251')
    p = re.compile(expr, re.IGNORECASE | re.LOCALE)
    string = string.encode('windows-1251')
    match = p.search(string)
    locale.setlocale(locale.LC_CTYPE, oldloc)
    if match:
        return True
    return False
