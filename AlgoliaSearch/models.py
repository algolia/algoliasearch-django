from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import models

from algoliasearch import algoliasearch


logger = logging.getLogger(__name__)


class AlgoliaIndexError(Exception):
    '''Something went wrong with an Algolia Index.'''


class AlgoliaIndex(object):
    '''An index in the Algolia backend.'''

    # Use to specify a custom field that will be used for the objectID.
    # This field should be unique.
    custom_objectID = None

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
        self.__client = client
        self.__set_index(client)

        all_fields = model._meta.get_all_field_names()

        # Avoid error when there is only one field to index
        if isinstance(self.fields, str):
            self.fields = (self.fields, )

        # Check fields
        for field in self.fields:
            if not (hasattr(model, field) or (field in all_fields)):
                raise AlgoliaIndexError(
                    '{} is not an attribute of {}.'.format(field, model))

        # If no fields are specified, index all the fields of the model
        if not self.fields:
            self.fields = all_fields
            self.fields.remove('id')

        # Check geo_field
        if self.geo_field:
            if hasattr(model, self.geo_field):
                attr = getattr(model, self.geo_field)
                if not (isinstance(attr, tuple) or callable(attr)):
                    raise AlgoliaIndexError(
                        '`geo_field` should be a tuple or a callable that returns a tuple.')
            else:
                raise AlgoliaIndexError('{} is not an attribute of {}.'.format(
                    self.geo_field, model))

        # Check custom_objectID
        if self.custom_objectID:
            if hasattr(model, self.custom_objectID):
                attr = getattr(model, elf.custom_objectID)
                if not isinstance(attr, str):
                    raise AlgoliaIndexError(
                        '`custom_objectID` should be a string.')
            else:
                raise AlgoliaIndex('`{}` is not an attribute of {}.'.format(
                    self.custom_objectID, model))

    def __set_index(self, client):
        '''Get an instance of Algolia Index'''
        if not self.index_name:
            self.index_name = self.model.__name__
        if hasattr(settings, 'ALGOLIA_INDEX_PREFIX'):
            self.index_name = settings.ALGOLIA_INDEX_PREFIX + '_' + self.index_name
        if hasattr(settings, 'ALGOLIA_INDEX_SUFFIX'):
            self.index_name += '_' + settings.ALGOLIA_INDEX_SUFFIX
        self.__index = client.init_index(self.index_name)
        self.__tmp_index = client.init_index(self.index_name + '_tmp')

    def __get_objectID(self, instance):
        '''Return the objectID of an instance.'''
        if self.custom_objectID:
            return getattr(instance, custom_objectID)
        else:
            return instance.pk

    def __build_object(self, instance):
        '''Build the JSON object.'''
        tmp = {'objectID': self.__get_objectID(instance)}
        if isinstance(self.fields, dict):
            for key, value in self.fields.items():
                attr = getattr(instance, key)
                if callable(attr):
                    attr = attr()
                tmp[value] = attr
        else:
            for field in self.fields:
                attr = getattr(instance, field)
                if callable(attr):
                    attr = attr()
                tmp[field] = attr

        if self.geo_field:
            attr = getattr(instance, self.geo_field)
            if callable(attr):
                attr = attr()
            tmp['_geoloc'] = {'lat': attr[0], 'lng': attr[1]}
        logger.debug('BUILD %s FROM %s', tmp['objectID'], self.model)
        return tmp

    def update_obj_index(self, instance):
        '''Update the object.'''
        obj = self.__build_object(instance)
        self.__index.save_object(obj)
        logger.debug('UPDATE %s FROM %s', obj['objectID'], self.model)

    def delete_obj_index(self, instance):
        '''Delete the object.'''
        objectID = self.__get_objectID(instance)
        self.__index.delete_object(objectID)
        logger.debug('DELETE %s FROM %s', objectID, self.model)

    def set_settings(self):
        '''Apply the settings to the index.'''
        if self.settings:
            self.__index.set_settings(self.settings)
            logger.debug('APPLY SETTINGS ON %s', self.index_name)

    def clear_index(self):
        '''Clear the index.'''
        self.__index.clear_index()
        logger.debug('CLEAR INDEX %s', self.index_name)

    def index_all(self, batch_size=1000):
        '''
        Index all records.
        This methods first resend the settings, then clear index and finally
        send all the records.
        '''
        self.set_settings()
        self.clear_index()

        counts = 0
        batch = []
        for instance in self.model.objects.all():
            batch.append(self.__build_object(instance))
            if len(batch) >= batch_size:
                self.__index.save_objects(batch)
                logger.info('SAVE %d OBJECTS TO %s', len(batch), self.index_name)
                batch = []
            counts += 1
        if len(batch) > 0:
            self.__index.save_objects(batch)
            logger.info('SAVE %d OBJECTS TO %s', len(batch), self.index_name)
        return counts

    def reindex_all(self, batch_size=1000):
        '''
        Reindex all records.
        This methods do the same as `index_all` but in a temporary index. Then
        the indexing task is finish, it moves the temporary index to the normal
        index.
        '''
        if self.settings:
            self.__tmp_index.set_settings(self.settings)
            logger.debug('APPLY SETTINGS ON %s_tmp', self.index_name)
        self.__tmp_index.clear_index()
        logger.debug('CLEAR INDEX %s_tmp', self.index_name)

        result = None
        counts = 0
        batch = []
        for instance in self.model.objects.all():
            batch.append(self.__build_object(instance))
            if len(batch) >= batch_size:
                result = self.__tmp_index.save_objects(batch)
                logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch), self.index_name)
                batch = []
            counts += 1
        if len(batch) > 0:
            result = self.__tmp_index.save_objects(batch)
            logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch), self.index_name)
        if result:
            self.__tmp_index.wait_task(result['taskID'])
            self.__client.move_index(self.index_name + '_tmp', self.index_name)
            logger.info('MOVE INDEX %s_tmp TO %s', self.index_name, self.index_name)
        return counts
