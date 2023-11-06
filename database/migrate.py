from models import *

tables = [Course, Lesson, Topics, UserCourse]

db.drop_tables(tables)
db.create_tables([Users] + tables)

base_topics = ['Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Программирование', 'Юриспруденция', 'Психология']
for i in base_topics:
    Topics.create(text=i)
