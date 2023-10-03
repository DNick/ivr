from models import *

tables = [Course, Lesson, Topics, CourseTopic, UserCourse]

db.drop_tables(tables)
db.create_tables([Users] + tables)

base_topics = ['Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Программирование', 'Юриспруденция', 'Психология']
for i in base_topics:
    Topics.create(text=i)

Course.create(
    user_id=1,
    title='первый курсик',
    description='подробное описание курса интересного очень'
)
Course.create(
    user_id=1,
    title='bruhbruhbruhbruhbruh',
    description='bruhbruhbruhbruhbruhbruhbruhbruhbruhvbruh'
)
