from flask import Flask

from pathlib import Path
import sys
sys.path.append(Path().absolute().parent.as_posix())
from spark import init_app

app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5000'


@app.route('/extra')
def extra():
    return "hmmm"

s = init_app(app)

with app.app_context():
    s.render_pages()


