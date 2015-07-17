'''
AlgoliaSearch integration for Django.
http://www.algolia.com
'''

from __future__ import unicode_literals

from . import models
from . import registration
from . import settings
from . import version

__version__ = version.VERSION
ALGOLIA_SETTINGS = settings.SETTINGS

AlgoliaIndex = models.AlgoliaIndex
AlgoliaEngine = registration.AlgoliaEngine
algolia_engine = registration.algolia_engine

# Algolia Engine functions

register = algolia_engine.register
unregister = algolia_engine.unregister
get_registered_model = algolia_engine.get_registered_models

get_adapter = algolia_engine.get_adapter
get_adapter_from_instance = algolia_engine.get_adapter_from_instance

raw_search = algolia_engine.raw_search
update_records = algolia_engine.update_records
