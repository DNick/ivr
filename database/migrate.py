from models import *

tables = [Users, Course, Lesson, Topics, UserCourse]

db.drop_tables(tables, cascade=True)
db.create_tables(tables)

base_topics = ['Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Информатика', 'Юриспруденция', 'Психология', 'Бизнес', 'Медиа', 'Профориентация', 'Анализ данных', 'Рыбалка']
for i in base_topics:
    Topics.create(text=i)
