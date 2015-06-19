Algolia Search for Django
==================

This package let you easily integrate the Algolia Search API to your favorite ORM. It's based on the [algoliasearch-client-python](https://github.com/algolia/algoliasearch-client-python) package. Both Python 2.x and 3.x are supported.

You might be interested in the sample Django application providing a typeahead.js based auto-completion and Google-like instant search: [algoliasearch-django-example](https://github.com/algolia/algoliasearch-django-example)

[![PyPI version](https://badge.fury.io/py/algoliasearch-django.svg)](http://badge.fury.io/py/algoliasearch-django)

Table of Content
-------------
**Get started**

1. [Install](#install)
1. [Setup](#setup)
1. [Quick Start](#quick-start)
1. [Commands](#commands)
1. [Search](#search)
1. [Geo-search](#geo-search)
1. [Options](#options)


Install
-------------

```sh
pip install algoliasearch-django
```

Setup
-------------

In your Django settings, add `django.contrib.algoliasearch` to `INSTALLED_APPS` and add two settings:

```python
ALGOLIA_APPLICATION_ID = 'MyAppID'
ALGOLIA_API_KEY = 'MyApiKey'
```

There is also two optionals settings that take a string:

* `ALGOLIA_INDEX_PREFIX`: prefix all index. You can use it to seperate different application, like `site1_Products` and `site2_Products`.
* `ALGOLIA_INDEX_SUFFIX`: suffix all index. You can use it to differenciate development and production environement, like `Location_dev` and `Location_prod`.


Quick Start
-------------

Simply call `AlgoliaSearch.register()` for each of the models you want to index. A good place to do this is in your application's AppConfig (generally named `apps.py`).

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

By default, all the fields of your model will be used. You can configure the index by creating a subclass of `AlgoliaIndex`. A good place to do this is in a separeted file, like `index.py`.

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

* `python manage.py algolia_buildindex`: index all the registered models. This one should be use the first time. Be careful, if the index already exist on Algolia, it will clear it first.
* `python manage.py algolia_reindex`: reindex all the registered models. This command will first send all the record to a temporary index and then moves it when the build operation is completed. **We highly recommand this command in production environement.**
* `python manage.py algolia_applysettings`: (re)apply the index settings.
* `python manage.py algolia_clearindex`: clear the index

## Search

We recommend the usage of our [JavaScript API Client](https://github.com/algolia/algoliasearch-client-js) to perform queries directly from the end-user browser without going through your server.

## Geo-Search

Use the `geo_field` attribute to localize your record. `geo_field` can be a tuple or a callable that return a tuple (latitude, longitude).

```python
class Contact(models.Model):
    name = models.CharField()
    lat = models.FloatField()
    lng = models.FloatField()
    
    def location(self):
        return (self.lat, self.lng)


class ContactIndex(AlgoliaIndex):
    fields = 'name'
    geo_field = 'location'


algoliasearch.register(Contact, ContactIndex)
```

# Options

## Custom `objectID`

You can choose which field will be used as the `objectID`. The field should be unique and can be a string or integer. By default, we use the `pk` field of the model.

```python
class ArticleIndex(AlgoliaIndex):
    custom_objectID = 'post_id'
```

## Custom index name

You can customize the inde name. By default, the index name will be the name of the model class.

```python
class ContactIndex(AlgoliaIndex):
    index_name = 'Entreprise'
```

## Index settings

We provide many ways to configure your index allowing you to tune your overall index relevancy. All the configuration are explained on [our website](https://www.algolia.com/doc/python#Settings).

```python
class ArticleIndex(AlgoliaIndex):
    settings = {
        'attributesToIndex': ['name', 'description', 'url'],
        'customRanking': ['desc(vote_count)', 'asc(name)']
    }
```