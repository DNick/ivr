from dotenv import dotenv_values
from peewee import *

env = dotenv_values()

try:
    db = PostgresqlDatabase(
        database=env['DB_NAME'],
        user=env['DB_USER'],
        password=env['DB_PASSWORD'],
        host=env['DB_HOST'],
    )
except Exception as exc:
    print(f'Не удалось подключиться к БД сервиса: {exc}')


class BaseModel(Model):
    class Meta:
        database = db


class Users(BaseModel):
    chat_id = TextField()
    attrs = TextField(default='{}')
    access_courses_token = TextField()


class Course(BaseModel):
    user_id = ForeignKeyField(Users)
    title = TextField()
    description = TextField()
    price = TextField(default=0)
    likes_count = BigIntegerField(default=0)
    likes_sum = BigIntegerField(default=0)
    views = BigIntegerField(default=0)
    have_logo = BooleanField(default=False)
    order_of_lessons = TextField(default='')


class Lesson(BaseModel):
    user_id = ForeignKeyField(Users)
    course_id = ForeignKeyField(Course)
    url = TextField()
    views = TextField(default=0)


class Topics(BaseModel):
    text = TextField()

# class CourseTopic(BaseModel):
#     course_id = ForeignKeyField(Course)
#     topic_id = ForeignKeyField(Topics)
