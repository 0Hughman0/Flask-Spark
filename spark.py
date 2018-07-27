from pathlib import Path
import os

from flask import render_template, current_app
from werkzeug.routing import Map, Rule
from jinja2 import FileSystemLoader, BaseLoader, TemplateNotFound, TemplatesNotFound


import importlib.util
import importlib


class _Page:
    render_func = render_template

    def __init__(self, folder, template, name=None, *args, **kwargs):
        self.folder = folder
        self.template = template
        if name is None:
            name = ''.join(self.template.split('.')[:-1])
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def render(self):
        return _Page.render_func(self.path.as_posix(), *self.args,
                                 page=self, folder=self.folder, **self.kwargs)

    @property
    def abs_path(self):
        return self.folder.abs_path / self.template

    @property
    def path(self):
        return self.folder.path / self.template

    @property
    def rel_url(self):
        return self.path.as_posix()


class SubDomain:

    pages_cls = _Page

    def __init__(self, __file__, name=None):
        """
        :param file: __file__
        """
        self.abs_path = Path(__file__).parent
        if name is None:
            name = self.abs_path.name
        self.name = name
        self.pages = []

    def Page(self, template, name=None, *args, **kwargs):
        page = SubDomain.pages_cls(self, template, name, *args, **kwargs)
        self.pages.append(page)
        return page

    @property
    def path(self):
        return self.abs_path.relative_to(current_app.config['PAGES_FOLDER'])

    @property
    def rel_url(self):
        path = self.path.as_posix()
        return path if path != '.' else ''

    def abs_file(self, filename):
        return self.abs_path / filename

    def file(self, filename):
        return self.path / filename


class FlaskSpark:

    def __init__(self, pages_path, url_prefix='/', output_dir='static'):
        self.pages_dir = Path(pages_path)
        self.url_prefix = url_prefix
        self.output_dir = Path(output_dir)
        self.pages = {}
        self.subdomains = {}

    @property
    def url_map(self):
        pages = [Rule(self.url_prefix + page.rel_url, endpoint=name) for name, page in self.pages.items()]
        subdomains = []
        for name, subdomain in self.subdomains.items():
            prefix = self.url_prefix + subdomain.rel_url
            if prefix == '/':
                prefix = ''
            subdomains.append(Rule(prefix + '/<path:filename>', endpoint=name))
        return Map(pages + subdomains)

    def spark_url(self, name, filename=None):
        map = self.url_map
        builder = map.bind('', self.url_prefix)
        return builder.build(name, {} if not filename else {'filename': filename})

    def render_pages(self):
        for page in self.pages.values():
            rendered_page = page.render()
            with open(self.output_dir / page.path, 'w') as f:
                f.write(rendered_page)

    def _find_pages(self, path, _pages):
        spec = importlib.util.spec_from_file_location('__init__.py', Path(path) / '__init__.py')
        mod = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(mod)
        except FileNotFoundError as e:
            return []

        subdomain = mod.__subdomain__
        _pages.extend(subdomain.pages)

        if subdomain.name in self.subdomains:
            raise KeyError("Subdomains with same name '{}' "
                           "(try setting name parameter for one or both)".format(subdomain.name))

        self.subdomains[subdomain.name] = subdomain

        for entry in os.scandir(path):
            if entry.is_dir():
                self._find_pages(entry, _pages) # recurse!

        return _pages

    def load_pages(self):
        if not self.pages_dir.is_dir():
            raise FileNotFoundError("Cannot find pages dir: {}".format(self.pages_dir))
        pages = self._find_pages(self.pages_dir, [])
        for page in pages:
            self.pages[page.name] = page


def init_app(app, pages_folder=None, url_prefix=None, spark_cls=FlaskSpark):
    if pages_folder is None:
        pages_folder = app.config.get('PAGES_FOLDER', 'pages')
    if url_prefix is None:
        url_prefix = app.config.get('URL_PREFIX', '/')

    pages_folder = Path(pages_folder)
    if not pages_folder.is_absolute():
        pages_folder = Path(app.root_path) / pages_folder

    app.config['PAGES_FOLDER'] = pages_folder
    app.config['URL_PREFIX'] = url_prefix

    s = spark_cls(pages_folder, url_prefix)
    s.load_pages()

    @app.context_processor
    def inject_spark_url():
        return {'spark_url': s.spark_url}

    @app.cli.command()
    def spark_render():
        s.render_pages()

    app.jinja_loader = QueueLoader([app.jinja_loader, FileSystemLoader(s.pages_dir.as_posix())])

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
