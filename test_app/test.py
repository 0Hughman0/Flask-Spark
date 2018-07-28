from flask import Flask, render_template

from pathlib import Path
import sys
sys.path.append(Path().absolute().parent.as_posix())
from spark import init_app

app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5000'


@app.route('/')
def extra():
    return render_template('extra.html')


s = init_app(app)

with app.app_context():
    s.load_pages()
    s.render_pages()
