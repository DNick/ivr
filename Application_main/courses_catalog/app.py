import sys, os
import time

from flask import Flask, render_template, request

# os.system('flask run')
sys.path.append('../../')
from database.models import Topics, Course

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    topics = list(map(lambda x: x.__data__, Topics.select()))
    courses = list(map(lambda x: x.__data__, Course.select()))
    if request.method == 'GET':
        return render_template('index.html', topics=topics, courses=courses)
    elif request.method == 'POST':
        pass


@app.route('/course/<int:course_id>/', methods=['GET', 'POST'])
def course(course_id):
    current_course = Course.get_by_id(course_id).__data__
    if request.method == 'GET':
        return render_template('course.html', course=current_course)




if __name__ == '__main__':
    app.run()
