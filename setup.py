import os
from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name = 'algoliasearch-django',
    version = '1.0.0',
    license = 'MIT License',
    packages = ['AlgoliaSearch'],
    install_requires = ['algoliasearch'],
    description = 'AlgoliaSearch integration for Django',
    long_description = README,
    author = 'Algolia Team',
    author_email = 'hey@algolia.com',
    url = 'https://github.com/algolia/algoliasearch-django',
    keywords = ['algolia', 'pyalgolia', 'search', 'backend', 'hosted', 'cloud',
        'full-text search', 'faceted search', 'django'],
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Interne :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Developement :: Libraries :: Python Modules'
    ]
)
