from dotenv import dotenv_values
from peewee import *

env = dotenv_values()

try:
    db = PostgresqlDatabase(
        host=env['DB_HOST'],
        database=env['DB_NAME'],
        user=env['DB_USER'],
        password=env['DB_PASSWORD']
    )

except Exception as exc:
    print(f'Не удалось подключиться к БД сервиса: {exc}')


class BaseModel(Model):
    class Meta:
        database = db


class Topics(BaseModel):
    text = TextField()


class Users(BaseModel):
    chat_id = TextField()
    attrs = TextField(default='{}')
    access_courses_token = TextField(default='')
    bank_card = TextField(null=True)


class Course(BaseModel):
    user_id = ForeignKeyField(Users)
    title = TextField()
    description = TextField()
    price = TextField(default=0)
    rate_count = BigIntegerField(default=0)
    rate_sum = BigIntegerField(default=0)
    views = BigIntegerField(default=0)
    have_logo = BooleanField(default=False)
    order_of_lessons = TextField(default='')
    publication_date = IntegerField(null=True)
    chat_url = TextField(default='')
    topic_id = ForeignKeyField(Topics, null=True)


class Lesson(BaseModel):
    user_id = ForeignKeyField(Users)
    course_id = ForeignKeyField(Course)
    url = TextField()
    views = TextField(default=0)


class UserCourse(BaseModel):  # Таблица записи на курс пользователем
    user_id = ForeignKeyField(Users)
    course_id = ForeignKeyField(Course)
