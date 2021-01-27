#!/usr/bin/env python

import os
import sys

from setuptools import setup
from setuptools import find_packages


# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

path_readme = os.path.join(os.path.dirname(__file__), 'README.md')
try:
    import pypandoc
    README = pypandoc.convert(path_readme, 'rst')
except (IOError, ImportError):
    with open(path_readme) as readme:
        README = readme.read()

path_version = os.path.join(os.path.dirname(__file__),
                            'algoliasearch_django/version.py')
if sys.version_info[0] == 3:
    exec(open(path_version).read())
else:
    execfile(path_version)


setup(
    name='algoliasearch-django',
    version=VERSION,
    license='MIT License',
    packages=find_packages(exclude=['tests']),
    install_requires=['django>=1.7', 'algoliasearch>=2.0,<3.0'],
    description='Algolia Search integration for Django',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Algolia Team',
    author_email='support@algolia.com',
    url='https://github.com/algolia/algoliasearch-django',
    keywords=['algolia', 'pyalgolia', 'search', 'backend', 'hosted', 'cloud',
              'full-text search', 'faceted search', 'django'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
