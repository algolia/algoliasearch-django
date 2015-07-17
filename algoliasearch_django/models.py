from __future__ import unicode_literals
from functools import partial
from itertools import chain
import logging

from algoliasearch.algoliasearch import AlgoliaException

from .settings import DEBUG

logger = logging.getLogger(__name__)
_getattr = lambda object, name: getattr(object, name)


def check_and_get_attr(model, name):
    try:
        attr = getattr(model, name)
        if callable(attr):
            return attr
        else:
            return get_model_attr(name)
    except AttributeError:
        raise AlgoliaIndexError(
            '{} is not an attribute of {}'.format(name, model))


def get_model_attr(name):
    return partial(_getattr, name=name)


class AlgoliaIndexError(Exception):
    '''Something went wrong with an Algolia Index.'''


class AlgoliaIndex(object):
    '''An index in the Algolia backend.'''

    # Use to specify a custom field that will be used for the objectID.
    # This field should be unique.
    custom_objectID = 'pk'

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

    def __init__(self, model, client, settings):
        '''Initializes the index.'''
        self.model = model
        self.__client = client
        self.__settings = settings
        self.__set_index(client)

        self.__named_fields = {}
        self.__translate_fields = {}
        all_model_fields = model._meta.get_all_field_names()

        if isinstance(self.fields, str):
            self.fields = (self.fields, )
        elif isinstance(self.fields, (list, tuple, set)):
            self.fields = tuple(self.fields)
        else:
            raise AlgoliaIndexError('Fields must be a str, list, tuple or set')

        # Check fields
        for field in self.fields:
            if isinstance(field, str):
                attr = field
                name = field
            elif isinstance(field, (list, tuple)) and len(field) == 2:
                attr = field[0]
                name = field[1]
            else:
                raise AlgoliaIndexError(
                    'Invalid fields syntax: {}'.format(field))

            self.__translate_fields[attr] = name
            if attr in all_model_fields:
                self.__named_fields[name] = get_model_attr(attr)
            else:
                self.__named_fields[name] = self.__check_and_get_attr(attr)

        # If no fields are specified, index all the fields of the model
        if not self.fields:
            self.fields = set(all_model_fields)
            for elt in ('pk', 'id', 'objectID'):
                try:
                    self.fields.remove(elt)
                except KeyError:
                    continue
            self.__translate_fields = dict(zip(self.fields, self.fields))
            self.__named_fields = dict(zip(self.fields, map(get_model_attr,
                                                            self.fields)))

        # Check custom_objectID
        if self.custom_objectID in chain(['pk'], all_model_fields):
            self.objectID = get_model_attr(self.custom_objectID)
        else:
            raise AlgoliaIndexError('{} is not a model field of {}'.format(
                self.custom_objectID, model))

        # Check tags
        if self.tags:
            if self.tags in all_model_fields:
                self.tags = get_model_attr(self.tags)
            else:
                self.tags = self.__check_and_get_attr(self.tags)

        # Check geo_field
        if self.geo_field:
            self.geo_field = self.__check_and_get_attr(self.geo_field)

        # Check should_index
        if self.should_index:
            self.should_index = self.__check_and_get_attr(self.should_index)

    def __check_and_get_attr(self, attr):
        return check_and_get_attr(self.model, attr)

    def __set_index(self, client):
        '''Get an instance of Algolia Index'''
        if not self.index_name:
            self.index_name = self.model.__name__

        if 'INDEX_PREFIX' in self.__settings:
            self.index_name = (self.__settings['INDEX_PREFIX'] + '_' +
                               self.index_name)
        if 'INDEX_SUFFIX' in self.__settings:
            self.index_name += '_' + self.__settings['INDEX_SUFFIX']

        self.__index = client.init_index(self.index_name)
        self.__tmp_index = client.init_index(self.index_name + '_tmp')

    def get_raw_record(self, instance, update_fields=None):
        '''Get the raw record (JSON).'''
        tmp = {'objectID': self.objectID(instance)}

        if update_fields:
            for elt in update_fields:
                key = self.__translate_fields.get(elt, None)
                if key:
                    tmp[key] = self.__named_fields[key](instance)
        else:
            for key, value in self.__named_fields.items():
                tmp[key] = value(instance)

            if self.geo_field:
                loc = self.geo_field(instance)
                tmp['_geoloc'] = {'lat': loc[0], 'lng': loc[1]}

            if self.tags:
                tmp['_tags'] = self.tags(instance)

        logger.debug('BUILD %s FROM %s', tmp['objectID'], self.model)
        return tmp

    def save_record(self, instance, update_fields=None, **kwargs):
        '''Save the object.'''
        if self.should_index:
            if not self.should_index(instance):
                # Should not index, but since we don't now the state of the
                # instance, we need to send a DELETE request to ensure that if
                # the instance was previously indexed, it will be removed.
                self.delete_obj(instance)
                return

        try:
            if update_fields:
                obj = self.get_raw_record(instance,
                                          update_fields=update_fields)
                self.__index.partial_update_object(obj)
            else:
                obj = self.get_raw_record(instance)
                self.__index.save_object(obj)
            logger.info('SAVE %s FROM %s', obj['objectID'], self.model)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s FROM %s NOT SAVED: %s', obj['objectID'],
                               self.model, e.message)

    def delete_record(self, instance):
        '''Delete the object.'''
        objectID = self.objectID(instance)
        try:
            self.__index.delete_object(objectID)
            logger.info('DELETE %s FROM %s', objectID, self.model)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s FROM %s NOT DELETED: %s', objectID,
                               self.model, e.message)

    def update_records(self, qs, batch_size=1000, **kwargs):
        '''
        Update multiple records of this index

        This method is optimized for speed. It takes a QuerySet and the same
        arguments as QuerySet.update(). Optionnaly, you can specify the size
        of the batch send to Algolia with batch_size (default to 1000).

        >>> from algoliasearch_django import update_records
        >>> qs = MyModel.objects.filter(myField=False)
        >>> update_records(MyModel, qs, myField=True)
        >>> qs.update(myField=True)
        '''
        tmp = {}
        for key, value in kwargs:
            name = self.__translate_fields.get(key, None)
            if name:
                tmp[name] = value

        batch = []
        for instance in qs.only(self.custom_objectID):
            tmp['objectID'] = self.objectID(instance)
            batch.append(dict(tmp))

            if len(batch) >= batch_size:
                self.__index.partial_update_objects(batch)
                batch = []

        if len(batch) > 0:
            self.__index.partial_update_objects(batch)

    def raw_search(self, query='', params={}):
        '''Return the raw JSON.'''
        try:
            return self.__index.search(query, params)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('ERROR DURING SEARCH: %s', e.message)

    def set_settings(self):
        '''Apply the settings to the index.'''
        if self.settings:
            try:
                self.__index.set_settings(self.settings)
                logger.info('APPLY SETTINGS ON %s', self.index_name)
            except AlgoliaException as e:
                if DEBUG:
                    raise e
                else:
                    logger.warning('SETTINGS NOT APPLYED ON %s: %s',
                                   self.model, e.message)

    def clear_index(self):
        '''Clear the index.'''
        try:
            self.__index.clear_index()
            logger.info('CLEAR INDEX %s', self.index_name)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s NOT CLEARED: %s', self.model, e.message)

    def reindex_all(self, batch_size=1000):
        '''Reindex all records.'''
        try:
            if self.settings:
                self.__tmp_index.set_settings(self.settings)
                logger.debug('APPLY SETTINGS ON %s_tmp', self.index_name)
            self.__tmp_index.clear_index()
            logger.debug('CLEAR INDEX %s_tmp', self.index_name)

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

                batch.append(self.get_raw_record(instance))
                if len(batch) >= batch_size:
                    self.__tmp_index.save_objects(batch)
                    logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch),
                                self.index_name)
                    batch = []
                counts += 1
            if len(batch) > 0:
                self.__tmp_index.save_objects(batch)
                logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch),
                            self.index_name)

            self.__client.move_index(self.__tmp_index.index_name,
                                     self.__index.index_name)
            logger.info('MOVE INDEX %s_tmp TO %s', self.index_name,
                        self.index_name)
            return counts
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('ERROR DURING REINDEXING %s: %s', self.model,
                               e.message)
