from __future__ import unicode_literals

from django.conf import settings
from django.db import models

from algoliasearch import algoliasearch


class AlgoliaIndexError(Exception):
    '''Something went wrong with an Algolia Index.'''

class AlgoliaIndex(object):
    '''An index in the Algolia backend.'''

    # Use to specify the fields that should be included in the index.
    fields = ()

    # Use to specify the geo-fields that should be used for location search.
    # The field should be a tuple or a callable that returns a tuple.
    geo_field = None

    # Use to specify the index to target on Algolia.
    index_name = None

    # Use to specify the settings of the index.
    settings = {}

    # Instance of the index from algoliasearch client
    __index = None

    def __init__(self, model, client):
        '''Initializes the index.'''
        self.model = model
        self.__set_index(client)

        all_fields = model._meta.get_all_field_names()

        # Avoid error when there is only one field to index
        if isinstance(self.fields, str):
            self.fields = (self.fields,)

        # Check the fields
        for field in self.fields:
            tmp = model()
            if callable(getattr(tmp, field)):
                pass
            elif field not in all_fields:
                raise AlgoliaIndexError('{} is not a field of {}'.format(
                    field, model
                ))

        # Check the geo_field
        if self.geo_field:
            attr = getattr(model, self.geo_field)
            if not (isinstance(attr, tuple) or callable(attr)):
                raise AlgoliaIndexError('`geo_field` should be a tuple or a callable that returns a tuple.')

        # If no fields are specified, index all the fields of the model
        if not self.fields:
            self.fields = all_fields
            self.fields.remove('id')

    def __set_index(self, client):
        '''Get an instance of Algolia Index'''
        if not self.index_name:
            self.index_name = self.model.__name__
        if settings.ALGOLIA_INDEX_PREFIX:
            self.index_name = settings.ALGOLIA_INDEX_PREFIX + '_' + self.index_name
        if settings.ALGOLIA_INDEX_SUFFIX:
            self.index_name += '_' + settings.ALGOLIA_INDEX_SUFFIX
        self.__index = client.init_index(self.index_name)

    def __build_object(self, instance):
        '''Build the JSON object.'''
        tmp = { 'objectID': instance.pk }
        for field in self.fields:
            attr = getattr(instance, field)
            if callable(attr):
                attr = attr()
            tmp[field] = attr
        if self.geo_field:
            attr = getattr(instance, self.geo_field)
            if callable(attr):
                attr = attr()
            tmp['_geoloc'] = { 'lat': attr[0], 'lng': attr[1] }
        return tmp

    def apply_settings(self):
        '''Apply the settings to the index.'''
        if self.settings:
            self.__index.set_settings(self.settings)

    def update_obj_index(self, instance):
        '''Update the object.'''
        obj = self.__build_object(instance)
        self.__index.save_object(obj)

    def delete_obj_index(self, instance):
        '''Delete the object.'''
        self.__index.delete_object(instance.pk)
