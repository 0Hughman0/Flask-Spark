from spark import Root
from flask import current_app

root = Root(__file__)
home = root.Home('home.html')
about = root.Page('about.html', render_kwargs={'app_name': current_app.name})

__root__ = root

from .posts import *
from .posts.new import *
