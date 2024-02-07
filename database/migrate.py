from models import *

tables = [Lesson, Topics, UserCourse, Course, Users]

db.drop_tables(tables, cascade=True)
db.create_tables(tables)

base_topics = ['Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Информатика', 'Юриспруденция', 'Психология', 'Бизнес', 'Медиа', 'Профориентация', 'Анализ данных', 'Здоровье', 'Рыбалка']
for i in base_topics:
    Topics.create(text=i)
