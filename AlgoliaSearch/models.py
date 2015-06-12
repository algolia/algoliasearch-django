from __future__ import unicode_literals


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

    def __init__(self, model):
        '''Initializes the index.'''
        self.model = model
