from models import *

tables = [Users, Course, Lesson, Topics]

db.drop_tables(tables)
db.create_tables(tables)

base_topics = ['Кулинария', 'Спорт', 'Красота', 'Музыка', 'Менеджмент', 'Финансы', 'Программирование', 'Юриспруденция', 'Психология']
for i in base_topics:
    Topics.create(text=i)
