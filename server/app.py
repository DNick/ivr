import sys

from dotenv import dotenv_values
from flask import Flask, render_template, request

from App_main.utils import get_logo_url_from_course_id, get_lessons_titles
from database.models import Topics, Course

app = Flask(__name__)
values = dotenv_values()


@app.route('/', methods=['GET', 'POST'])
def index():
    topics = list(map(lambda x: x.__data__, Topics.select()))
    courses = map(lambda x: x.__data__, Course.select().where(bool(Course.publication_date)))
    courses = list(map(lambda x: modify_course_fields(x), courses))

    if request.method == 'POST':
        title = request.form['title']
        chosen_topics = request.form.getlist('topics')
        sorting = request.form['sorting'].split('_')[-1]
        courses = list(filter(lambda course: title.lower() in course['title'].lower(), courses))
        if chosen_topics:
            courses = list(filter(lambda x: x['topic_text'] in chosen_topics and x['topic_text'], courses))
        courses = my_sorting(courses, sorting)

    return render_template('index.html', topics=topics, courses=courses)


@app.route('/course/<int:course_id>/', methods=['GET', 'POST'])
def course(course_id):
    current_course = Course.get_by_id(course_id).__data__
    current_course['lessons_titles'] = get_lessons_titles(current_course['order_of_lessons'])
    if current_course['have_logo']:
        current_course['logo_url'] = get_logo_url_from_course_id(course_id)

    if request.method == 'GET':
        return render_template('course.html',
                               index_page_url=values['INDEX_PAGE_URL'],
                               course=current_course)


def my_sorting(courses, sorting):
    trans = {
        'date': ('publication_date', -1),
        'rate': ('average_rate', -1),
        'price': ('price', 1)
    }
    return list(sorted(courses, key=lambda x: trans[sorting][1] * x[trans[sorting][0]]))


def modify_course_fields(course):
    try:
        course['topic_text'] = Topics.get_by_id(course['topic_id']).text
    except:
        course['topic_text'] = ''
    if course['rate_count'] == 0:
        average_rate = 0
    else:
        average_rate = round(course['rate_sum'] / course['rate_count'], 1)
    course['average_rate'] = average_rate
    if int(average_rate) == average_rate:
        course['average_rate'] = int(average_rate)

    return course


if __name__ == '__main__':
    app.run('localhost', 8000)
