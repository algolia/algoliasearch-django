Algolia Search for Django
==================

This package let you easily integrate the Algolia Search API to your favorite ORM. It's based on the [algoliasearch-client-python](https://github.com/algolia/algoliasearch-client-python) package. Both Python 2.x and 3.x are supported.

You might be interested in the sample Django application providing a typeahead.js based auto-completion and Google-like instant search: (algoliasearch-django-example)[] (TODO)

TODO: travis + other badges

Table of Content
-------------
**Get started**

1. [Install](#install)
1. [Setup](#setup)
1. [Quick Start](#quick-start)

Install
-------------

```sh
pip install algoliasearch-django
```

Setup
-------------

In your Django settings, add `AlgoliaSearch` to `INSTALLED_APPS` and add two settings:

```python
ALGOLIA_APPLICATION_ID = 'MyAppID'
ALGOLIA_API_KEY = 'MyApiKey'
```

TODO: speak about prefix/suffix usage

Quick Start
-------------

Simply call `AlgoliaSearch.register()` for each of the models you want to index. A good place to do this is in your application's AppConfig (generally your `app.py` file):

```python
from django.apps import AppConfig
import AlgoliaSearch

class YourAppConfig(AppConfig):
    name = 'your_app'

    def ready(self):
        YourModel = self.get_model('your_model')
        AlgoliaSearch.register(YourModel)
```

By default, all the fields of your model will be used. You can configure the index by creating a subclass of `AlgoliaIndex`. A good place to do this is in a separeted file `index.py`:

```python
from AlgoliaSearch import AlgoliaIndex

class YourModelIndex(AlgoliaIndex):
    fields = ('name', 'date',) # default: all the fields of your model
    geo_field = 'location' # tuple or callable that returns tuple (lat, lng)
    settings = {'attributesToIndex': ['name']} # index settings
    index_name = 'my_index' # default: model.__name__
```

`fields` and `geo_field` can be a field or a callable.
Please take a look at [the documentation about index settings](https://www.algolia.com/doc/python#Settings). `settings` is applied when the command `algolia_buildindex`, `algolia_reindex` or `algolia_applysettings` is executed.





## Setup

* Install via pip: `pip install algoliasearch-django`
* In your `setting.py`, add `AlgoliaSearch` to the `INTALLED_APPS`
* In the same file, adds to variable `ALGOLIA_APPLICATION_ID` and `ALGOLIA_API_KEY`
* Register your model in your AppConfig
* Run the command to index the models: `python manage.py algolia_buildindex`

## Settings

* `ALGOLIA_INDEX_PREFIX`: a prefix for all the index (useful for diff app)
* `ALGOLIA_INDEX_SUFFIX`: a suffix for all the index (useful for dev/prod/test)
* `ALGOLIA_APPLICATION_ID`: your application ID
* `ALGOLIA_API_KEY`: your API key (need write access)

## Commands

* `./manage.py algolia_buildindex`: hard index all the models
* `./manage.py algolia_reindex`: solf reindex all the models (create another index, send data, wait the indexing task and then rename the index)
