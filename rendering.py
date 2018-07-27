def create_blogpost(post_dir, info):
    """
    Creates a fully initialised BlogPost Object loaded from a directory. Should be the primary route to creating
    BlogPost objects.

    Secretly adds to database and flushes (needed to get id# and subsequently create static path).
    As a result of this REQUIRES DATABASE COMMIT AFTER USING.
    :param post_dir: pathlib.Path pointing to path to load from.
    :return: initialised blogpost object.
    
    Not sure about this one
    """

    title = info['title']
    category = info['category']
    created = info['created']

    tags = info.get('tags', "")
    description = info.get('description', "")

    thumbnail = info.get('thumbnail')

    blogpost = BlogPost(title=title, description=description,
                        category=category, tags=tags,
                        from_dir=post_dir, created=created, thumbnail=thumbnail)

    return blogpost


def render_blogpost(blogpost):
    md = markdown.Markdown(
        extensions=[HughDunnitMdExt(post=blogpost), FencedCodeExtension(), 'markdown.extensions.codehilite'])
    with open((blogpost.raw_path / "article.md").as_posix(), encoding='utf-8') as article_f:
        raw_article = md.convert(article_f.read())

    raw_article_html = render_template_string(raw_article, post=blogpost)
    tree = ET.fromstring(raw_article_html)
    preview_html = '\n'.join(ET.tostring(e, encoding='utf-8').decode("utf-8") for e, _ in zip(tree, range(4)))

    article_html = render_template("page.html",
                                   post=blogpost, post_html=raw_article_html,
                                   page_title=blogpost.title, title=blogpost.category.name)
    preview_html = render_template("preview.html", post=blogpost, preview_html=preview_html)

    # raw_text = tree.text_content()
    return article_html, preview_html
