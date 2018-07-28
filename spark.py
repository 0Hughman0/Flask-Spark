"""
(c) Hugh Ramsden 2018

Flask Spark
-----------
Bring together dynamic and static sites driven by Flask

Flask spark aims to make it easier to build a flask site with static pages integrated.

It allows the flask templating engine to be used to render static templates.

It also provides an erm... novel way of defining the structure of your static site.

Attributes
----------
pages_classes : mapping
    a global level dictionary that you can add subclasses of _Page to, which allows them to easily be used by any
    Folder. (see `_Folder` docstring)
"""

import itertools
from pathlib import Path

from flask import render_template, current_app, render_template_string

from werkzeug.routing import Map, Rule
from jinja2 import FileSystemLoader, BaseLoader, TemplateNotFound, TemplatesNotFound

from markdown import Markdown

import importlib

from markdown_ext import MdExt

page_classes = {}


class _Page:
    """
    Encapsulates a static page from site.

    Handles information about where the page template is, as well as implements rendering of the template.

    Attributes
    ==========
    root : Root
        root folder (shared amongst all instance of _Page!)

    Warning
    =======
    This class shouldn't be created directly! Instead should be created by a Folder instance
    (facilitates tracking parents/ root)
    """

    root = None

    def __init__(self, folder, template, name=None, render_args=None, render_kwargs=None):
        """
        Encapsulates a static page from site.

        Handles information about where the page template is, as well as implements rendering of the template.

        Parameters
        ==========
        folder : _Folder
            folder that template lives in.
        template : str
            name of template file within same folder as `folder`.
        name : str
            name of template, used as 'endpoint' for `spark_url` (defaults to None, if None, will take name of template
            file (without suffix!)
        render_args : iterable
            positional arguments to be passed to render function
        render_kwargs : mapping
            key word arguments to be passed to render function

        Attributes
        ==========
        abs_path
        path
        rel_url
        folder : _Folder
            folder template lives in
        template : str
            name of template file within same folder as `folder`.
        name : str
            name of template, used as 'endpoint' for `spark_url` (defaults to None, if None, will take name of template
            file (without suffix!)
        render_args : iterable
            positional arguments to be passed to render function
        render_kwargs : mapping
            key word arguments to be passed to render function

        Warning
        =======
        This class shouldn't be created directly! Instead should be created by a Folder instance
        (facilitates tracking parents/ root)
        """
        self.folder = folder
        self.template = template
        if name is None:
            name = ''.join(self.template.split('.')[:-1])
        self.name = name
        self.render_args = render_args if render_args else tuple()
        self.render_kwargs = render_kwargs if render_kwargs else dict()

    def render(self):
        """
        render function.

        called by FlaskSpark object when rendering pages.

        Uses flasks `render_template` method to perform rendering

        Returns
        =======
        page : str
            string containing html ready to be written to output directory!

        Notes
        =====
        passes `self.render_args` and `self.render_kwargs` as parameters to `render_template` function.
        Additionally passes `page=self` as keyword argument... as I think this could be useful.. not sure why!
        """
        return render_template(self.path.as_posix(), *self.render_args,
                               page=self, **self.render_kwargs)

    @property
    def abs_path(self):
        """
        Returns
        =======
        path : pathlib.Path
            absolute path to template
        """
        return self.folder.abs_path / self.template

    @property
    def path(self):
        """
        Returns
        =======
        path : pathlib.Path
            relative path to template (relative to Root folder)
        """
        return self.abs_path.relative_to(self.root.abs_path)

    @property
    def rel_url(self):
        """
        Returns
        -------
        url : str
            relative url from Root (is actually just `self.path.as_posix()`!
        """
        return self.path.as_posix()

    def __repr__(self):
        return "<Page {}>".format(self.rel_url)


class _MarkdownPage(_Page):
    """
    Subclass of _Page - for rendering markdown templates

    Attributes
    ----------
    extensions : list
        list of default markdown extensions. defaults:
            * fenced code - allows fenced code blocks
            * codehilite - adds compatibility with pylint (if installed!)
            * MdExt - custom ext see markdown_ext.py
    """

    extensions = ['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', MdExt()]

    def render(self):
        """
        Render markdown template into HTML.

        Returns
        -------
        page : str
            string of HTML render of template

        Notes
        -----
        Rendering of markdown files performed first. Generated HTML is then 're-rendered' by
        Flask's `render_template_string` function.

        Some effort is made to allow Jinja Flow control blocks/ template inheritance to still be used, though it's not
        exactly well tested! read - you can still use `{% xyz %}` and {{ xyz }} within `.md` templates!
        """
        md = Markdown(extensions=_MarkdownPage.extensions)

        with open(self.abs_path, encoding='utf-8') as page_md:
            page_html = md.convert(page_md.read())

        return render_template_string(page_html, *self.render_args,
                                      page=self, **self.render_kwargs)


page_classes['Page'] = _Page
page_classes['MarkdownPage'] = _MarkdownPage


class _Folder:
    """
    Represents a folder/ submount within static site tree

    Attributes
    ----------
    root : _Root
        reference to root of static site tree
    page_classes : mapping
        dictionary containing different Page types (allows for new page types to easily be added) see spark.py docstring

    Notes
    -----
    Any Page classes added to the global `page_classes` dictionary can be accessed e.g.

    ```python
    # add new page class
    page_classes['MyPage'] = _MyPage
    # ...
    # accessed with
    folder.MyPage(...)
    ```
    """

    root = None
    pages_classes = page_classes

    def __init__(self, file, name=None):
        """
        Represents a folder/ submount within static site tree

        Parameters
        ----------
        file : str
            __file__ from file in directory within static site tree.
        name : str
            name used as endpoint in `spark_url`. (See `FlaskSpark.spark_url`). Default - takes name of directory

        Attributes
        ----------
        abs_path : pathlib.Path
            absolute path to directory
        name : str
            name used as endpoint in `spark_url`. (See `FlaskSpark.spark_url`). Default - takes name of directory
        pages : list
            list of `_Page` objects within that folder
        """
        self.abs_path = Path(file).parent
        if name is None:
            name = self.abs_path.name
        self.name = name
        self.pages = []

    def __getattr__(self, item):
        """implements creating Page classes from page_classes dict"""
        if item in self.pages_classes:
            def make_page(template, name=None, render_args=None, render_kwargs=None):
                page = self.pages_classes[item](self, template, name, render_args, render_kwargs)
                page.root = self.root
                self.pages.append(page)
            make_page.__name__ = item
            return make_page
        raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__, item))

    @property
    def path(self):
        """
        Returns
        -------
        path : pathlib.Path
            relative path to folder
        """
        return self.abs_path.relative_to(self.root.abs_path)

    @property
    def rel_url(self):
        """
        Returns
        -------
        url : str
            relative url from Root (is actually just `self.path.as_posix()`!
        """
        return self.path.as_posix()

    def __repr__(self):
        return "<Folder {}>".format(self.rel_url)


class Root(_Folder):
    """
    Subclass of _Folder which defines the root directory/ url in static site!
    """

    def __init__(self, file, name='root'):
        """
        Subclass of _Folder which defines the root directory/ url in static site!

        Parameters
        ----------
        file : str
            __file__ from file in directory within static site tree.
        name : str
            name used as endpoint in `spark_url`. (See `FlaskSpark.spark_url`). Default - takes name of directory

        Attributes
        ----------
        abs_path : pathlib.Path
            absolute path to directory
        name : str
            name used as endpoint in `spark_url`. (See `FlaskSpark.spark_url`). Default - 'root'
        pages : list
            list of `_Page` objects within that folder
        home : _Page
            special _Page designed as doc returned from root url. (Set using `root.Home`).
        folders : list
            list of all the folders below root (self).
        """
        super().__init__(file, name)
        self.folders = []
        self.home = None
        self.root = self

    @property
    def rel_url(self):
        """
        Returns
        -------
        url : str
            root url (always '/')
        """
        return '/'

    def Folder(self, file, name=None):
        """
        Factory for creating new _Folder instances (sets `_Folder.root = self`)!

        Parameters
        ----------
        file : str
            __file__ from file in directory within static site tree.
        name : str
            name used as endpoint in `spark_url`. (See `FlaskSpark.spark_url`). Default - takes name of directory

        Returns
        -------
        folder : _Folder
            `_Folder` object with `self` as root
        """
        folder = _Folder(file, name)
        folder.root = self
        self.folders.append(folder)
        return folder

    def Home(self, template, name=None, render_args=None, render_kwargs=None):
        """
        Create _Page object to use as `self.home` for '/' route.

        Parameters
        ==========
        folder : _Folder
            folder that template lives in.
        template : str
            name of template file within same folder as `folder`.
        name : str
            name of template, used as 'endpoint' for `spark_url` (defaults to None, if None, will take name of template
            file (without suffix!)
        render_args : iterable
            positional arguments to be passed to render function
        render_kwargs : mapping
            key word arguments to be passed to render function

        Returns
        -------
        page : _Page
            page object
        """
        page = Root.pages_classes['Page'](self, template, name, render_args=render_args, render_kwargs=render_kwargs)
        page.root = self
        self.home = page
        return page

    @property
    def map(self):
        """
        Generate url map for all folders and pages belonging to `self`. Used to deduce urls in `spark_url`.

        Returns
        -------
        map : werkzeug.routing.Map
            Map of each url and corresponding endpoint
        """
        rules = [Rule('/', endpoint=self.home.name),
                 Rule('/<path:filename>', endpoint=self.root.name)]
        for page in self.pages: # root's pages!
            rules.append(Rule('/' + page.rel_url, endpoint=page.name))

        for folder in self.folders: # other folder's pages
            rules.append(Rule('/' + folder.rel_url + '/<path:filename>', endpoint=folder.name))
            for page in folder.pages:
                rules.append(Rule('/' + page.rel_url, endpoint=page.name))
        return Map(rules)

    def iter_pages(self):
        """flat iterator for every page under root.
        """
        return itertools.chain((self.home,), self.pages, *(folder.pages for folder in self.folders))

    def __repr__(self):
        return "<Root {}>".format(self.rel_url)


class FlaskSpark:
    """
    Performs rendering and file operations.

    Takes care of interactions with current_app.

    #Todo
    Implement mirroring pages filesystem in output_folder! - including copying over non-template files.
    """

    def __init__(self, pages_folder, url_prefix='static/', output_folder='static'):
        """
        Performs rendering and file operations.

        Takes care of interactions with current_app.

        Parameters
        ----------
        pages_folder : str or pathlib.Path
            *absolute* path to folder to be treated as root for static site.
        url_prefix : str
            prefix to apply to urls (useful if want static site to be under submount) defaults to 'static/' so that
            normal flask app can serve files from static folder! (needs to end in '/' but not start with one!).
        output_folder : str or pathlib.Path
            path to directory where filled in templates are saved. At present you need to manually add subdirectories to
            match that of pages folder as no way of creating folders is implemented. defaults to static once again to
            make it easy to serve rendered templates with default flask app.

        Attributes
        ----------
        pages_folder : pathlib.Path
            *absolute* path to folder to be treated as root for static site.
        url_prefix : str
            prefix to apply to urls (useful if want static site to be under submount) defaults to 'static/' so that
            normal flask app can serve files from static folder! (needs to end in '/' but not start with one!).
        output_folder : pathlib.Path
            path to directory where filled in templates are saved. At present you need to manually add subdirectories to
            match that of pages folder as no way of creating folders is implemented. defaults to static once again to
            make it easy to serve rendered templates with default flask app.
        root : Root
            root object from pages dir (only set upon calling load_pages!)
        """
        self.pages_folder = Path(pages_folder)
        self.url_prefix = url_prefix
        self.output_folder = Path(output_folder)
        self.root = None

    def spark_url(self, name, filename=None):
        """
        Emulating flask's `url_for` but for FlaskSpark templates!

        Parameters
        ----------
        name : str
            name corresponding to endpoint that you want a url for (see _Page, _Folder and _Root constructors!)
        filename : str
            the name of a static file from Folder specified by `name` you want a url for.

        Returns
        -------
        url : str
            full url to resource you want

        Notes
        -----
        To generate urls `spark_url` must be called within an application or request context, as it needs access to
        current app for config options.

        app.config['SERVER_NAME'] Must be set for `spark_url` to work!
        """
        if current_app.config['SERVER_NAME'] is None:
            raise RuntimeError(
                'Application was not able to create a URL adapter for request'
                ' independent URL generation. You might be able to fix this by'
                ' setting the SERVER_NAME config variable.'
            )
        map = self.root.map
        script_name = current_app.config['APPLICATION_ROOT']
        if script_name is None:
            script_name = '/'
        builder = map.bind(current_app.config['SERVER_NAME'],
                           script_name=script_name + self.url_prefix,
                           url_scheme=current_app.config['PREFERRED_URL_SCHEME'])
        return builder.build(name, {} if not filename else {'filename': filename}, force_external=True)

    def render_pages(self):
        """
        Render each Page under `self.root`, and write to `self.output_folder`
        """
        for page in self.root.iter_pages():
            rendered_page = page.render()
            with open(self.output_folder / page.path.with_suffix('.html'), 'w') as f:
                f.write(rendered_page)

    def _find_pages(self, path):
        """
        Nauty method for loading the templates from pages directory.

        Monkey patches `sys.path` and then undos the change... is there a better way to do this!?
        """
        import sys
        sys.path.append(path.parent.as_posix())
        pages = importlib.import_module(path.name)
        self.root = pages.__root__
        sys.path.pop(-1)

    def load_pages(self):
        """
        Loads pages... well really just discovers `self.root`

        Simply tries to import package found at `self.pages_folder`, then checks for `__root__` attribute and
        assigns that to `self.root`!
        """
        if not self.pages_folder.is_dir():
            raise FileNotFoundError("Cannot find pages dir: {}".format(self.pages_folder))
        self._find_pages(self.pages_folder)


def init_app(app, pages_folder=None, url_prefix='static/', output_folder='static', spark_cls=FlaskSpark):
    """
    Initialise FlaskSpark.

    Does a bit of monkeypatching of `app` to make FlaskSpark work.
        1. it adds the context processor `spark_url` which is meant to serve as a substitute for `url_for` when getting urls
           for static pages
        2. adds the cli command `spark_render` which re-renders all of the templates etc. found in
           `FlaskSpark.pages_folder`
        3. swaps out the standard `Flask.jinja_loader` for `QueueLoader` which allows `render_template` to work with
           templates found in `pages` folder by adding a FileSystemLoader pointing to `root` as a fallback for the
           default loader!

    Parameters
    ----------
    app : Flask
        flask app you want to use FlaskSpark with
    pages_folder : str or pathlib.Path
            *absolute* path to folder to be treated as root for static site.
    url_prefix : str
        prefix to apply to urls (useful if want static site to be under submount) defaults to 'static/' so that
        normal flask app can serve files from static folder! (needs to end in '/' but not start with one!).
    output_folder : str or pathlib.Path
        path to directory where filled in templates are saved. At present you need to manually add subdirectories to
        match that of pages folder as no way of creating folders is implemented. defaults to static once again to
        make it easy to serve rendered templates with default flask app.
    spark_cls : class
        just there just in case you want to provide your own subclass of FlaskSpark for some reason!

    Returns
    -------
    spark : FlaskSpark
        FlaskSpark instance!
    """
    if pages_folder is None:
        pages_folder = app.config.get('PAGES_FOLDER', 'pages')
    if url_prefix is None:
        url_prefix = app.config.get('URL_PREFIX', '')

    pages_folder = Path(pages_folder)
    if not pages_folder.is_absolute():
        pages_folder = Path(app.root_path) / pages_folder

    app.config['PAGES_FOLDER'] = pages_folder
    app.config['URL_PREFIX'] = url_prefix

    s = spark_cls(pages_folder, url_prefix, output_folder)

    @app.context_processor
    def inject_spark_url():
        return {'spark_url': s.spark_url}

    @app.cli.command()
    def spark_render():
        s.load_pages()
        s.render_pages()

    app.jinja_loader = QueueLoader([app.jinja_loader, FileSystemLoader(s.pages_folder.as_posix())])

    return s


class QueueLoader(BaseLoader):

    def __init__(self, loader_queue):
        """
        Template loader that tries each loader in the queue, until one doesn't raise a template error
        """
        self.loaders = loader_queue

    def get_source(self, environment, template):
        exception = None
        for loader in self.loaders:
            try:
                return loader.get_source(environment, template)
            except (TemplateNotFound, TemplatesNotFound) as e:
                exception = e
        raise exception
