# Flask Spark
### Bridging the gap between static and dynamic flavoured flask apps

Flask Spark aims to make it easier to add static content to a flask app. To do this, it makes the powerful Jinja2
templating engine available to static templates outside of your regular flask app called `Pages`.

To build up the structure of your static site you simply have to fill up your `pages` directory with templates in the
structure of your static site.

E.g:

    pages
    │   about.html
    │   markdown.md
    │   __init__.py
    ├───info
            info1.html
           __init__.py

Your `pages` folder actually acts like a Python package which makes it easier to integrate with your
dynamic application. Your `pages` package simply needs a few configuration lines to tell Flask-Spark how to
render your templates. In your top level `__init__.py` file, you create a `Root` object, that all of your `Page` objects
are created from (In the background this allows Flask Spark to work out the structure of your website).

    from spark import Root
    from flask import current_app

    root = Root(__file__)
    root.Page('about.html', render_kwargs={'app_name': current_app.name})

    __root__ = root

    from .info import * # this looks a bit strange, but it just makes sure pages in directories below are added!

For any levels below `root`, you build up that submount in a similar way, by creating `Folder` objects:

    from .. import root

    folder = root.Folder(__file__)
    folder.Page('info1.html')

Then simply initialise your app with:

    from spark import init_app
    from flask import Flask

    app = Flask(__name__)
    app.config['SERVER_NAME'] = '127.0.0.1:5000'

    spark = init_app(app)

Behind the scenes this does a bit of work that ultimately allows you to run the cli command `spark_render`:

    ..\my_app$ flask spark_render

This command then renders, each page in `pages` using flask's own `render_template` method. Finally these html documents
get written to an output folder, ready to be served up.

## Additional features:

* Builtin `MarkdownPage` type that can render markdown templates. Additionally, flask spark makes a bit of effort to
ensure Jinja flow control such as `{% for i in range(10) %}` and `{% extends 'master.html' %}` still works!
* Use of `url_for` within your static templates is maintained, making it easy to link to your dynamic site.
* Additionally a `spark_url` context processor is provided, which emulates `url_for`'s behaviour, but builds urls for
content within the static site. (`spark_url` can also be used within the dynamic application).
