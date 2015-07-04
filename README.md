Algolia Search for Django
==================

This package lets you easily integrate the Algolia Search API to your [Django](https://www.djangoproject.com/) project. It's based on the [algoliasearch-client-python](https://github.com/algolia/algoliasearch-client-python) package.

You might be interested in this sample Django application providing a typeahead.js based auto-completion and Google-like instant search: [algoliasearch-django-example](https://github.com/algolia/algoliasearch-django-example)

Compatible with **Python 2.7**, **Python 3.2+** and **Django 1.7+**

[![Build Status](https://travis-ci.org/algolia/algoliasearch-django.svg?branch=master)](https://travis-ci.org/algolia/algoliasearch-django)
[![Coverage Status](https://coveralls.io/repos/algolia/algoliasearch-django/badge.svg?branch=master)](https://coveralls.io/r/algolia/algoliasearch-django)
[![PyPI version](https://badge.fury.io/py/algoliasearch-django.svg?branch=master)](http://badge.fury.io/py/algoliasearch-django)

Table of Content
-------------
**Get started**

1. [Install](#install)
1. [Setup](#setup)
1. [Quick Start](#quick-start)
1. [Commands](#commands)
1. [Search](#search)
1. [Geo-search](#geo-search)
1. [Tags](#tags)
1. [Options](#options)


Install
-------------

```sh
pip install algoliasearch-django
```

Setup
-------------

In your Django settings, add `django.contrib.algoliasearch` to `INSTALLED_APPS` and add these two settings:

```python
ALGOLIA = {
    'APPLICATION_ID': 'MyAppID',
    'API_KEY': 'MyApiKey'
}
```

There are two optional settings:

* `INDEX_PREFIX`: prefix all indexes. Use it to separate different applications, like `site1_Products` and `site2_Products`.
* `INDEX_SUFFIX`: suffix all indexes. Use it to differenciate development and production environment, like `Location_dev` and `Location_prod`.


Quick Start
-------------

Simply call `AlgoliaSearch.register()` for each of the models you want to index. A good place to do this is in your application's AppConfig (generally named `apps.py`). More info in the [documentation](https://docs.djangoproject.com/en/1.8/ref/applications/)

```python
from django.apps import AppConfig
from django.contrib import algoliasearch

class YourAppConfig(AppConfig):
    name = 'your_app'

    def ready(self):
        YourModel = self.get_model('your_model')
        algoliasearch.register(YourModel)
```

And then, don't forget the line below in the `__init__.py` file of your Django application.

```python
default_app_config = 'your_django_app.apps.YourAppConfig'
```

By default, all the fields of your model will be used. You can configure the index by creating a subclass of `AlgoliaIndex`. A good place to do this is in a separate file, like `index.py`.

```python
from django.contrib.algoliasearch import AlgoliaIndex

class YourModelIndex(AlgoliaIndex):
    fields = ('name', 'date')
    geo_field = 'location'
    settings = {'attributesToIndex': ['name']}
    index_name = 'my_index'
```

And then replace `algoliasearch.register(YourModel)` with `algoliasearch.register(YourModel, YourModelIndex)`.

## Commands

* `python manage.py algolia_reindex`: reindex all the registered models. This command will first send all the record to a temporary index and then moves it.
* `python manage.py algolia_applysettings`: (re)apply the index settings.
* `python manage.py algolia_clearindex`: clear the index

## Search

We recommend the usage of our [JavaScript API Client](https://github.com/algolia/algoliasearch-client-js) to perform queries directly from the end-user browser without going through your server.

However, if you want to search from your backend you can use the `raw_search(YourModel, 'yourQuery', params)` method. It retrieves the raw JSON answer from the API.

```python
from django.contrib.algoliasearch import raw_search

params = { "hitsPerPage": 5 }
raw_search(Contact, "jim", params)
```

## Geo-Search

Use the `geo_field` attribute to localize your record. `geo_field` should be a callable that returns a tuple (latitude, longitude).

```python
class Contact(models.model):
    name = models.CharField(max_lenght=20)
    lat = models.FloatField()
    lng = models.FloatField()

    def location(self):
        return (self.lat, self.lng)


class ContactIndex(AlgoliaIndex):
    fields = 'name'
    geo_field = 'location'


algoliasearch.register(Contact, ContactIndex)
```

# Tags

Use the `tags` attributes to add tags to your record. It can be a field or a callable.

```python
class ArticleIndex(AlgoliaIndex):
    tags = 'category'
```

At query time, specify `{ tagFilters: 'tagvalue' }` or `{ tagFilters: ['tagvalue1', 'tagvalue2'] }` as search parameters to restrict the result set to specific tags.

# Options

## Custom `objectID`

You can choose which field will be used as the `objectID `. The field should be unique and can be a string or integer. By default, we use the `pk` field of the model.

```python
class ArticleIndex(AlgoliaIndex):
    custom_objectID = 'post_id'
```

## Custom index name

You can customize the index name. By default, the index name will be the name of the model class.

```python
class ContactIndex(algoliaindex):
    index_name = 'Entreprise'
```

## Index settings

We provide many ways to configure your index allowing you to tune your overall index relevancy. All the configuration is explained on [our website](https://www.algolia.com/doc/python#Settings).

```python
class ArticleIndex(AlgoliaIndex):
    settings = {
        'attributesToIndex': ['name', 'description', 'url'],
        'customRanking': ['desc(vote_count)', 'asc(name)']
    }
```

## Restrict indexing to a subset of your data

You can add constraints controlling if a record must be indexed or not. `should_index` should be a callable that returns a boolean.

```python
class Contact(models.model):
    name = models.CharField(max_lenght=20)
    age = models.IntegerField()

    def is_adult(self):
        return (self.age >= 18)

class ContactIndex(AlgoliaIndex):
    should_index = 'is_adult'
```
