import io
from typing import Dict

import requests
from telebot import SimpleCustomFilter
import json

from Application_for_creators.tables import *
from config import bot, s3
from database.models import Users, Course
from PIL import Image
from dotenv import dotenv_values

values = dotenv_values()


class StateFilter(SimpleCustomFilter):
    key = 'state'

    def check(self, obj):
        if not hasattr(obj, 'chat'):
            obj = obj.message
        return get_user_attr(obj.chat.id, 'state')


class EditingCourseFilter(SimpleCustomFilter):
    key = 'is_edit_course'

    def check(self, obj):
        if not hasattr(obj, 'chat'):
            obj = obj.message
        return get_user_attr(obj.chat.id, 'current_course') != ''


def is_non_negative_digit(text):
    return text.isdigit() and int(text) >= 0


def set_user_attr(chat_id, attr, data):
    attrs_str = Users.get(Users.chat_id == chat_id).attrs
    attrs_dict = json.loads(attrs_str)
    attrs_dict[attr] = data
    query = Users.update({Users.attrs: json.dumps(attrs_dict)}).where(Users.chat_id == chat_id)
    query.execute()


def set_state(chat_id, state):
    set_user_attr(chat_id, 'state', state)


def delete_state(chat_id):
    set_user_attr(chat_id, 'state', '')


def get_state(chat_id):
    return get_user_attr(chat_id, 'state')


def get_user_attrs(chat_id) -> Dict:
    return json.loads(Users.get(Users.chat_id == chat_id).attrs)


def get_user_attr(chat_id, attr):
    try:
        state_json = json.loads(Users.get(Users.chat_id == chat_id).attrs)
        if attr in state_json.keys():
            return state_json[attr]
    except:
        return ''


def is_image_square(file_id):
    image = get_image_from_file_id(file_id)
    return image.width == image.height


def crop_photo_to_square(file_id):
    image = get_image_from_file_id(file_id)
    delta = (image.width - image.height) // 2
    if delta < 0:
        cropped_image = image.crop((0, -delta, image.width, image.height + delta))
    elif delta > 0:
        cropped_image = image.crop((delta, 0, image.width - delta, image.height))

    return cropped_image


def get_image_from_file_id(file_id):
    resp = requests.get(
        bot.get_file_url(file_id),
        stream=True)
    return Image.open(resp.raw)


def save_course(msg, file_id=''):
    try:
        user_id = Users.select().where(Users.chat_id == msg.chat.id)[0].id
    except:
        bot.send_message(msg.chat.id, 'Вас нет в базе пользователей, нажмите /start, и попробуйте снова')
        return

    action = get_user_attr(msg.chat.id, 'action')
    current_course_id = get_user_attr(msg.chat.id, 'current_course')
    if not action or 'change_logo' not in action:
        user_attrs = get_user_attrs(msg.chat.id)
        new_course = Course.create(
            user_id=user_id,
            title=user_attrs['title'],
            description=user_attrs['description'],
            price=user_attrs['price'],
            have_logo=bool(file_id)
        )
        set_user_attr(msg.chat.id, 'current_course', int(new_course.get_id()))
        current_course_id = new_course.get_id()
        bot.send_message(msg.chat.id, 'Курс создан, теперь вы можете добавлять новые темы',
                         reply_markup=edit_course_table)
    else:
        bot.send_message(msg.chat.id, 'Фотография успешно изменена',
                         reply_markup=edit_course_table)

    delete_state(msg.chat.id)

    if file_id != '':
        logo = crop_photo_to_square(file_id)
        stream = io.BytesIO()
        logo.save(stream, 'JPEG')
        stream.seek(0)
        s3.upload_fileobj(stream, 'mybacket', f'logos/{current_course_id}.jpg')


def get_image_from_s3(backet, path):
    obj = s3.get_object(Bucket=backet, Key=path)
    return Image.open(obj['Body'])
