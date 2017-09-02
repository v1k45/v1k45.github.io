#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Vikas Yadav'
SITENAME = "v1k45"
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Asia/Kolkata'

DEFAULT_LANG = 'en'


STATIC_PATHS = ['pdfs', 'images']

INDEX_SAVE_AS = 'blog/index.html'

PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'

ARTICLE_URL = 'blog/{slug}/'
ARTICLE_SAVE_AS = 'blog/{slug}/index.html'

AUTHOR_URL = 'blog/authors/{slug}/'
AUTHOR_SAVE_AS = 'blog/authors/{slug}/index.html'

AUTHORS_URL = 'blog/authors/'
AUTHORS_SAVE_AS = 'blog/authors/index.html'

CATEGORY_URL = 'blog/categories/{slug}/'
CATEGORY_SAVE_AS = 'blog/categories/{slug}/index.html'

CATEGORIES_URL = 'blog/categories/'
CATEGORIES_SAVE_AS = 'blog/categories/index.html'

TAG_URL = 'blog/tags/{slug}/'
TAG_SAVE_AS = 'blog/tags/{slug}/index.html'

TAGS_URL = 'blog/tags/'
TAGS_SAVE_AS = 'blog/tags/index.html'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

THEME = 'sakura'

# Blogroll
LINKS = (('blog', '/blog/'),
         ('github', 'https://github.com/v1k45'),
         ('stackoverflow', 'http://stackoverflow.com/users/4726598/v1k45'),)

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
