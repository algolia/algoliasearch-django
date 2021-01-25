"""
AlgoliaSearch integration for Django.
http://www.algolia.com
"""

from django.utils.module_loading import autodiscover_modules

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

save_record = algolia_engine.save_record
delete_record = algolia_engine.delete_record
update_records = algolia_engine.update_records
raw_search = algolia_engine.raw_search
clear_index = algolia_engine.clear_index # TODO: deprecate
clear_objects = algolia_engine.clear_objects
reindex_all = algolia_engine.reindex_all

# Default log handler
import logging


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def autodiscover():
    autodiscover_modules('index')


logging.getLogger(__name__.split('.')[0]).addHandler(NullHandler())

default_app_config = 'algoliasearch_django.apps.AlgoliaConfig'
