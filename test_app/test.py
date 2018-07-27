from flask import Flask

import sys
sys.path.append(r"D:\Documents\Programin\WorkingVersions\flask_spark\flask_spark")
from spark import init_app

app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5000'


@app.route('/extra')
def extra():
    return "hmmm"

s = init_app(app)

with app.app_context():
    s.render_pages()


