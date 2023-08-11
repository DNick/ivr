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


if __name__ == '__main__':
    app.run()
