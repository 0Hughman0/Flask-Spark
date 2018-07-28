import re

from markdown.postprocessors import Postprocessor
from markdown.extensions import Extension


pattern = re.compile(r'(<p>)([\s]*?{%[\w\W]*?%}[\s]*?)(</p>)') # match {% %} inside <p> blocks (ish!)


class JinjaFlowFixer(Postprocessor):
    """
    Finds jinja template flow statements, and takes them out of <p> blocks!

    e.g. stops:

    '''

    {% for i in 'team' %}

    '''

    converting to

    '''
    <p>{% for i in 'team'%}</p>
    '''
    """

    def run(self, text):
        def replace(match):
            return match.group(2)

        return pattern.sub(replace, text)


class MdExt(Extension):

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.postprocessors.add('JinjaFlowFixer', JinjaFlowFixer(), '_end')
