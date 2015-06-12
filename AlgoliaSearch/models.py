from __future__ import unicode_literals

from django.conf import settings

from algoliasearch import algoliasearch


class AlgoliaIndex(objet):
    '''An index in the Algolia backend.'''

    # Use to specify the fields that should be included in the index.
    fields = ()

    # Use to specify the geo-fields that should be used for location search.
    geo_fields = ()

    # Use to specify the index to target on Algolia.
    index_name = ()

    # Use to specify the settings of the index.
    settings = {}

    # Instance of the index from algoliasearch client
    _index = None

    def __init__(self, model):
        '''Initializes the index.'''
        self.model = model

    def set_index(self, client):
        if not self.index_name:
            self.index_name = self.model.__name__
        if settings.ALGOLIA_INDEX_PREFIX:
            self.index_name += settings.ALGOLIA_INDEX_PREFIX
        self._index = client.init_index(self.index_name)
