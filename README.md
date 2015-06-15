# algoliasearch-django

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
