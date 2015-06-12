'''
AlgoliaSearch integration for Django.
http://www.algolia.com
'''

from __future__ import unicode_literals

from AlgoliaSearch.models import AlgoliaIndex
from AlgoliaSearch.registration import AlgoliaEngine, algolia_engine

register = algolia_engine.register
unregister = algolia_engine.unregister
get_registered_model = algolia_engine.get_registered_models
get_adapter = algolia_engine.get_adapter
