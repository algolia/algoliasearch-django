from __future__ import unicode_literals
from django.conf import settings
import logging

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
    # The attribute should be a callable that returns a tuple.
    geo_field = None

    # Use to specify the field that should be used for filtering by tag.
    tags = None

    # Use to specify the index to target on Algolia.
    index_name = None

    # Use to specify the settings of the index.
    settings = {}

    # Use to specify a callable that say if the instance should be indexed.
    # The attribute should be a callable that returns a boolean.
    should_index = None

    # Instance of the index from algoliasearch client
    __index = None

    def __init__(self, model, client):
        '''Initializes the index.'''
        self.model = model
        self.__client = client
        self.__set_index(client)

        try:
            all_fields = [f.name for f in model._meta.get_fields()]
        except AttributeError:  # Django 1.7
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

        # Check custom_objectID
        if self.custom_objectID:
            if not (hasattr(model, self.custom_objectID) or
                    (self.custom_objectID in all_fields)):
                raise AlgoliaIndexError('{} is not an attribute of {}.'.format(
                    self.custom_objectID, model))

        # Check tags
        if self.tags:
            if not (hasattr(model, self.tags) or (self.tags in all_fields)):
                raise AlgoliaIndexError('{} is not an attribute of {}'.format(
                    self.tags, model))

        # Check geo_field + get the callable
        if self.geo_field:
            if hasattr(model, self.geo_field):
                attr = getattr(model, self.geo_field)
                if callable(attr):
                    self.geo_field = attr
                else:
                    raise AlgoliaIndexError('{} should be a callable.'.format(
                        self.geo_field))
            else:
                raise AlgoliaIndexError('{} is not an attribute of {}.'.format(
                    self.geo_field, model))

        # Check should_index + get the callable
        if self.should_index:
            if hasattr(model, self.should_index):
                attr = getattr(model, self.should_index)
                if callable(attr):
                    self.should_index = attr
                else:
                    raise AlgoliaIndexError('{} should be a callable.'.format(
                        self.should_index))
            else:
                raise AlgoliaIndexError('{} is not an attribute of {}.'.format(
                    self.should_index, model))

    def __set_index(self, client):
        '''Get an instance of Algolia Index'''
        params = getattr(settings, 'ALGOLIA', None)

        if not self.index_name:
            self.index_name = self.model.__name__

        if params:
            if 'INDEX_PREFIX' in params:
                self.index_name = params['INDEX_PREFIX'] + '_' + self.index_name
            if 'INDEX_SUFFIX' in params:
                self.index_name += '_' + params['INDEX_SUFFIX']
        else:
            # @Deprecated: 1.1.0
            if hasattr(settings, 'ALGOLIA_INDEX_PREFIX'):
                self.index_name = settings.ALGOLIA_INDEX_PREFIX + '_' + self.index_name
            if hasattr(settings, 'ALGOLIA_INDEX_SUFFIX'):
                self.index_name += '_' + settings.ALGOLIA_INDEX_SUFFIX

        self.__index = client.init_index(self.index_name)
        self.__tmp_index = client.init_index(self.index_name + '_tmp')

    def __get_objectID(self, instance):
        '''Return the objectID of an instance.'''
        if self.custom_objectID:
            attr = getattr(instance, self.custom_objectID)
            if callable(attr):
                attr = attr()
            return attr
        else:
            return instance.pk

    def _build_object(self, instance):
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
            loc = self.geo_field(instance)

            if loc:
                tmp['_geoloc'] = {'lat': loc[0], 'lng': loc[1]}

        if self.tags:
            attr = getattr(instance, self.tags)
            if callable(attr):
                attr = attr()
            if not isinstance(attr, list):
                attr = list(attr)
            tmp['_tags'] = attr

        logger.debug('BUILD %s FROM %s', tmp['objectID'], self.model)
        return tmp

    def update_obj_index(self, instance):
        '''Update the object.'''
        if self.should_index:
            if not self.should_index(instance):
                # Should not index, but since we don't now the state of the
                # instance, we need to send a DELETE request to ensure that if
                # the instance was previously indexed, it will be removed.
                self.delete_obj_index(instance)
                return

        obj = self._build_object(instance)
        self.__index.save_object(obj)
        logger.debug('UPDATE %s FROM %s', obj['objectID'], self.model)

    def delete_obj_index(self, instance):
        '''Delete the object.'''
        objectID = self.__get_objectID(instance)
        self.__index.delete_object(objectID)
        logger.debug('DELETE %s FROM %s', objectID, self.model)

    def raw_search(self, query='', params={}):
        '''Return the raw JSON.'''
        return self.__index.search(query, params)

    def set_settings(self):
        '''Apply the settings to the index.'''
        if self.settings:
            self.__index.set_settings(self.settings)
            logger.debug('APPLY SETTINGS ON %s', self.index_name)

    def clear_index(self):
        '''Clear the index.'''
        self.__index.clear_index()
        logger.debug('CLEAR INDEX %s', self.index_name)

    def reindex_all(self, batch_size=1000):
        '''Reindex all records.'''
        if self.settings:
            self.__tmp_index.set_settings(self.settings)
            logger.debug('APPLY SETTINGS ON %s_tmp', self.index_name)
        self.__tmp_index.clear_index()
        logger.debug('CLEAR INDEX %s_tmp', self.index_name)

        result = None
        counts = 0
        batch = []

        if hasattr(self, 'get_queryset'):
            qs = self.get_queryset()
        else:
            qs = self.model.objects.all()

        for instance in qs:
            if self.should_index:
                if not self.should_index(instance):
                    continue  # should not index

            batch.append(self._build_object(instance))
            if len(batch) >= batch_size:
                result = self.__tmp_index.save_objects(batch)
                logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch),
                            self.index_name)
                batch = []
            counts += 1
        if len(batch) > 0:
            result = self.__tmp_index.save_objects(batch)
            logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch),
                        self.index_name)
        if result:
            self.__client.move_index(self.index_name + '_tmp', self.index_name)
            logger.info('MOVE INDEX %s_tmp TO %s', self.index_name,
                        self.index_name)
        return counts
