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
    access_courses_token = TextField()


class Course(BaseModel):
    user_id = ForeignKeyField(Users, backref='users')
    title = TextField()
    description = TextField()



class Lesson(BaseModel):
    course_id = ForeignKeyField(Course, backref='course')
    url = TextField()


class Topics(BaseModel):
    text = TextField()
