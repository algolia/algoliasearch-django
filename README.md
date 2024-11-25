<p align="center">
  <a href="https://www.algolia.com">
    <img alt="Algolia for Django" src="https://raw.githubusercontent.com/algolia/algoliasearch-client-common/master/banners/django.png" >
  </a>

  <h4 align="center">The perfect starting point to integrate <a href="https://algolia.com" target="_blank">Algolia</a> within your Django project</h4>

  <p align="center">
    <a href="https://travis-ci.org/algolia/algoliasearch-django"><img src="https://travis-ci.org/algolia/algoliasearch-django.svg?branch=master" alt="Build Status"></img></a>
    <a href="https://coveralls.io/r/algolia/algoliasearch-django"><img src="https://coveralls.io/repos/algolia/algoliasearch-django/badge.svg?branch=master" alt="Coverage Status"></img></a>
    <a href="http://badge.fury.io/py/algoliasearch-django"><img src="https://badge.fury.io/py/algoliasearch-django.svg?branch=master" alt="PyPi Version"></img></a>
  </p>
</p>

<p align="center">
  <a href="https://www.algolia.com/doc/framework-integration/django/options/?language=python" target="_blank">Documentation</a>  •
  <a href="https://discourse.algolia.com" target="_blank">Community Forum</a>  •
  <a href="http://stackoverflow.com/questions/tagged/algolia" target="_blank">Stack Overflow</a>  •
  <a href="https://github.com/algolia/algoliasearch-django/issues" target="_blank">Report a bug</a>  •
  <a href="https://www.algolia.com/doc/framework-integration/django/faq/" target="_blank">FAQ</a>  •
  <a href="https://www.algolia.com/support" target="_blank">Support</a>
</p>

## API Documentation

You can find the full reference on [Algolia's website](https://www.algolia.com/doc/framework-integration/django/).

1. **[Setup](#setup)**

   - [Introduction](#introduction)
   - [Install](#install)
   - [Setup](#setup)
   - [Quick Start](#quick-start)

1. **[Commands](#commands)**

   - [Commands](#commands)

1. **[Search](#search)**

   - [Search](#search)

1. **[Geo-Search](#geo-search)**

   - [Geo-Search](#geo-search)

1. **[Tags](#tags)**

   - [Tags](#tags)

1. **[Options](#options)**

   - [Custom <code>objectID</code>](#custom-codeobjectidcode)
   - [Custom index name](#custom-index-name)
   - [Field Preprocessing and Related objects](#field-preprocessing-and-related-objects)
   - [Index settings](#index-settings)
   - [Restrict indexing to a subset of your data](#restrict-indexing-to-a-subset-of-your-data)
   - [Multiple indices per model](#multiple-indices-per-model)
   - [Temporarily disable the auto-indexing](#temporarily-disable-the-auto-indexing)

1. **[Tests](#tests)**

   - [Run Tests](#run-tests)

1. **[Troubleshooting](#troubleshooting)**
   - [Frequently asked questions](#frequently-asked-questions)

# Setup

## Introduction

This package lets you easily integrate the Algolia Search API to your [Django](https://www.djangoproject.com/) project. It's based on the [algoliasearch-client-python](https://github.com/algolia/algoliasearch-client-python) package.

You might be interested in this sample Django application providing a typeahead.js based auto-completion and Google-like instant search: [algoliasearch-django-example](https://github.com/algolia/algoliasearch-django-example).

- Compatible with **Python 3.8+**.
- Supports **Django 4.x** and **5.x**.

## Install

```sh
pip install algoliasearch-django
```

## Setup

In your Django settings, add `algoliasearch_django` to `INSTALLED_APPS` and add these two settings:

```python
ALGOLIA = {
    'APPLICATION_ID': 'MyAppID',
    'API_KEY': 'MyApiKey'
}
```

There are several optional settings:

- `INDEX_PREFIX`: prefix all indices. Use it to separate different applications, like `site1_Products` and `site2_Products`.
- `INDEX_SUFFIX`: suffix all indices. Use it to differentiate development and production environments, like `Location_dev` and `Location_prod`.
- `AUTO_INDEXING`: automatically synchronize the models with Algolia (default to **True**).
- `RAISE_EXCEPTIONS`: raise exceptions on network errors instead of logging them (default to **settings.DEBUG**).

## Quick Start

Create an `index.py` inside each application that contains the models you want to index.
Inside this file, call `algoliasearch.register()` for each of the models you want to index:

```python
# index.py

import algoliasearch_django as algoliasearch

from .models import YourModel

algoliasearch.register(YourModel)
```

By default, all the fields of your model will be used. You can configure the index by creating a subclass of `AlgoliaIndex` and using the `register` decorator:

```python
# index.py

from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import YourModel

@register(YourModel)
class YourModelIndex(AlgoliaIndex):
    fields = ('name', 'date')
    geo_field = 'location'
    settings = {'searchableAttributes': ['name']}
    index_name = 'my_index'

```

# Commands

## Commands

- `python manage.py algolia_reindex`: reindex all the registered models. This command will first send all the record to a temporary index and then moves it.
  - you can pass `--model` parameter to reindex a given model
- `python manage.py algolia_applysettings`: (re)apply the index settings.
- `python manage.py algolia_clearindex`: clear the index

# Search

## Search

We recommend using our [InstantSearch.js library](https://www.algolia.com/doc/guides/building-search-ui/what-is-instantsearch/js/) to build your search
interface and perform search queries directly from the end-user browser without going through your server.

However, if you want to search from your backend you can use the `raw_search(YourModel, 'yourQuery', params)` method.
It retrieves the raw JSON answer from the API, and accepts in `param` any
[search parameters](https://www.algolia.com/doc/api-reference/search-api-parameters/).

```python
from algoliasearch_django import raw_search

params = { "hitsPerPage": 5 }
response = raw_search(Contact, "jim", params)
```

# Geo-Search

## Geo-Search

Use the `geo_field` attribute to localize your record. `geo_field` should be a callable that returns a tuple (latitude, longitude).

```python
class Contact(models.model):
    name = models.CharField(max_length=20)
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

## Tags

Use the `tags` attributes to add tags to your record. It can be a field or a callable.

```python
class ArticleIndex(AlgoliaIndex):
    tags = 'category'
```

At query time, specify `{ tagFilters: 'tagvalue' }` or `{ tagFilters: ['tagvalue1', 'tagvalue2'] }` as search parameters to restrict the result set to specific tags.

# Options

## Custom `objectID`

You can choose which field will be used as the `objectID `. The field should be unique and can
be a string or integer. By default, we use the `pk` field of the model.

```python
class ArticleIndex(AlgoliaIndex):
    custom_objectID = 'post_id'
```

## Custom index name

You can customize the index name. By default, the index name will be the name of the model class.

```python
class ContactIndex(algoliaindex):
    index_name = 'Enterprise'
```

## Field Preprocessing and Related objects

If you want to process a field before indexing it (e.g. capitalizing a `Contact`'s `name`),
or if you want to index a [related object](https://docs.djangoproject.com/en/1.11/ref/models/relations/)'s
attribute, you need to define **proxy methods** for these fields.

### Models

```python
class Account(models.Model):
    username = models.CharField(max_length=40)
    service = models.CharField(max_length=40)

class Contact(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField(max_length=60)
    //...
    accounts = models.ManyToManyField(Account)

    def account_names(self):
        return [str(account) for account in self.accounts.all()]

    def account_ids(self):
        return [account.id for account in self.accounts.all()]
```

### Index

```python
from algoliasearch_django import AlgoliaIndex

class ContactIndex(AlgoliaIndex):
    fields = ('name', 'email', 'company', 'address', 'city', 'county',
              'state', 'zip_code', 'phone', 'fax', 'web', 'followers', 'account_names', 'account_ids')

    settings = {
        'searchableAttributes': ['name', 'email', 'company', 'city', 'county', 'account_names',
        }
```

- With this configuration, you can search for a `Contact` using its `Account` names
- You can use the associated `account_ids` at search-time to fetch more data from your
  model (you should **only proxy the fields relevant for search** to keep your records' size
  as small as possible)

## Index settings

We provide many ways to configure your index allowing you to tune your overall index relevancy.
All the configuration is explained on [our doc](https://www.algolia.com/doc/api-reference/api-parameters/).

```python
class ArticleIndex(AlgoliaIndex):
    settings = {
        'searchableAttributes': ['name', 'description', 'url'],
        'customRanking': ['desc(vote_count)', 'asc(name)']
    }
```

## Restrict indexing to a subset of your data

You can add constraints controlling if a record must be indexed or not. `should_index` should be a
callable that returns a boolean.

```python
class Contact(models.model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()

    def is_adult(self):
        return (self.age >= 18)

class ContactIndex(AlgoliaIndex):
    should_index = 'is_adult'
```

## Multiple indices per model

It is possible to have several indices for a single model.

- First, define all your indices that you want for a model:

```python
from algoliasearch_django import AlgoliaIndex

class MyModelIndex1(AlgoliaIndex):
    name = 'MyModelIndex1'
    ...

class MyModelIndex2(AlgoliaIndex):
    name = 'MyModelIndex2'
    ...
```

- Then, define a meta model which will aggregate those indices:

```python
class MyModelMetaIndex(AlgoliaIndex):
    def __init__(self, model, client, settings):
        self.indices = [
            MyModelIndex1(model, client, settings),
            MyModelIndex2(model, client, settings),
        ]

    def raw_search(self, query='', params=None):
        res = {}
        for index in self.indices:
            res[index.name] = index.raw_search(query, params)
        return res

    def update_records(self, qs, batch_size=1000, **kwargs):
        for index in self.indices:
            index.update_records(qs, batch_size, **kwargs)

    def reindex_all(self, batch_size=1000):
        for index in self.indices:
            index.reindex_all(batch_size)

    def set_settings(self):
        for index in self.indices:
            index.set_settings()

    def clear_objects(self):
        for index in self.indices:
            index.clear_objects()

    def save_record(self, instance, update_fields=None, **kwargs):
        for index in self.indices:
            index.save_record(instance, update_fields, **kwargs)

    def delete_record(self, instance):
        for index in self.indices:
            index.delete_record(instance)
```

- Finally, register this `AlgoliaIndex` with your `Model`:

```python
import algoliasearch_django as algoliasearch
algoliasearch.register(MyModel, MyModelMetaIndex)
```

## Temporarily disable the auto-indexing

It is possible to temporarily disable the auto-indexing feature using the `disable_auto_indexing` context decorator:

```python
from algoliasearch_django.decorators import disable_auto_indexing

# Used as a context manager
with disable_auto_indexing():
    MyModel.save()

# Used as a decorator
@disable_auto_indexing():
my_method()

# You can also specifiy for which model you want to disable the auto-indexing
with disable_auto_indexing(MyModel):
    MyModel.save()
    MyOtherModel.save()

```

# Tests

## Run Tests

To run the tests, first find your Algolia application id and Admin API key (found on the Credentials page).

```shell
ALGOLIA_APPLICATION_ID={APPLICATION_ID} ALGOLIA_API_KEY={ADMIN_API_KEY} tox
```

To override settings for some tests, use the [settings method](https://docs.djangoproject.com/en/1.11/topics/testing/tools/#django.test.SimpleTestCase.settings):

```python
class OverrideSettingsTestCase(TestCase):
    def setUp(self):
        with self.settings(ALGOLIA={
            'APPLICATION_ID': 'foo',
            'API_KEY': 'bar',
            'AUTO_INDEXING': False
        }):
            algolia_engine.reset(settings.ALGOLIA)

    def tearDown(self):
        algolia_engine.reset(settings.ALGOLIA)

    def test_foo():
        # ...
```

# Troubleshooting

# Use the Dockerfile

If you want to contribute to this project without installing all its dependencies, you can use our Docker image. Please check our [dedicated guide](DOCKER_README.md) to learn more.

## Frequently asked questions

Encountering an issue? Before reaching out to support, we recommend heading to our [FAQ](https://www.algolia.com/doc/framework-integration/django/faq/) where you will find answers for the most common issues and gotchas with the package.
