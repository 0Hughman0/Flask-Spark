from .. import root
from flask import current_app

folder = root.Folder(__file__)
two = folder.Page('about.html', 'two')
md = folder.MarkdownPage('markdown.md')