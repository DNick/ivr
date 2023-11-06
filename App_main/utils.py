from datetime import datetime

from telegraph import Telegraph
from xlrd import xldate_as_datetime

from App_creators.config import s3
from database.models import Lesson

DOMAIN = 'https://telegra.ph/'

def get_logo_url_from_course_id(course_id):
    """
    :param course_id: Id курса
    :return: Фотка курса
    """
    url = s3.generate_presigned_url('get_object', Params={'Bucket': 'mybacket',
                                                            'Key': f'logos/{course_id}.jpg'})
    return url


def get_lessons_titles(order_of_lessons):
    """
    :param order_of_lessons: Id уроков через пробел в нужном порядке
    :return: Названия уроков
    """
    result = []
    for lesson_id in order_of_lessons.split():
        telegraph = Telegraph()
        path = Lesson.get_by_id(lesson_id).url[len(DOMAIN):]
        result.append(telegraph.get_page(path)['title'])
    return result


def standard_date_to_excel_date(date):
    """
    :param date: Дата
    :return: Преобразованная дата в excel формат
    """
    start = datetime(1899, 12, 30).date()
    delta = date - start
    return delta.days


def excel_date_to_standard_date(date):
    """
    :param date: Дата в excel формате
    :return: Преобразованная дата в Python объект
    """
    return xldate_as_datetime(date, 0).date()

