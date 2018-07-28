# Flask Spark
### Bring together dynamic and static sites driven by Flask

Flask spark aims to make it easier to build a flask site with static pages integrated.

It allows the flask templating engine to be used to render static templates.

It also provides an erm... novel way of defining the structure of your static site.

Flask spark tries to give you good value per line!

Creating your static site structure is as simple as filling a directory tree:

    pages
    │   about.html
    │   markdown.md
    │   __init__.py
    ├───info
            info1.html
           __init__.py

To make flask_spark aware of your structure the top level `pages/__init__.py` contains:

    from spark import Root
    from flask import current_app

    root = Root(__file__)
    root.Page('about.html', render_kwargs={'app_name': current_app.name})

    __root__ = root

    from .info import *

(Note that you can access the current app, and use it to fill in your templates!)

and `pages/info/__init__.py` contains:

    from .. import root

    folder = root.Folder(__file__)
    folder.Page('info1.html')

Then simply initialise your app with:

    from spark import init_app
    from flask import Flask

    app = Flask(__name__)
    app.config['SERVER_NAME'] = '127.0.0.1:5000'

    spark = init_app(app)

This then allows you to run the cli command `spark_render`:

    ..\my_app$ flask spark_render

which re-renders all templates from `pages`, and writes them to a configured directory.

flask spark also knows how to render markdown articles, and makes a bit of effort to ensure Jinja flow control such as
`{% for i in range(10) %}` and {% extends 'master.html' %} still works!

flask spark also allows you to use `url_for` within your static templates. Additionally it provides a `spark_url`
context processor, which lets you easily reference static pages within both static and app templates.
