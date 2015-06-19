'''
AlgoliaSearch integration for Django.
http://www.algolia.com
'''

from __future__ import unicode_literals

from django.contrib.algoliasearch.models import AlgoliaIndex
from django.contrib.algoliasearch.registration import AlgoliaEngine, algolia_engine

register = algolia_engine.register
unregister = algolia_engine.unregister
get_registered_model = algolia_engine.get_registered_models
get_adapter = algolia_engine.get_adapter
