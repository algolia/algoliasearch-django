import os
from distutils.core import setup


setup(
    name = 'algoliasearch-django',
    version = '1.0.0',
    description = '',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    author = 'Algolia',
    url = 'https://github.com/algolia/algoliasearch-django',
)
