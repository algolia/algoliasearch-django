from __future__ import unicode_literals

import inspect
from functools import partial
from itertools import chain
import logging
import types

import sys
from algoliasearch.exceptions import AlgoliaException
from django.db.models.query_utils import DeferredAttribute
try:
    from django.utils.inspect import func_supports_parameter, func_accepts_kwargs
except ImportError:  # Django 1.7
    from .utils import func_supports_parameter, func_accepts_kwargs

from .settings import DEBUG

logger = logging.getLogger(__name__)


def _getattr(obj, name):
    return getattr(obj, name)


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
    """Something went wrong with an Algolia Index."""


class AlgoliaIndex(object):
    """An index in the Algolia backend."""

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
    settings = None

    # User to specify a duplication method
    duplication_method = None

    # Used to specify if the instance should be indexed.
    # The attribute should be either:
    # - a callable that returns a boolean.
    # - a BooleanField
    # - a boolean property or attribute
    should_index = None

    # Name of the attribute to check on instances if should_index is not a callable
    _should_index_is_method = False

    DEFAULT_BATCH_SIZE = 1000

    def __init__(self, model, client, settings):
        """Initializes the index."""
        self.__init_index(client, model, settings)

        self.model = model
        self.__client = client
        self.__named_fields = {}
        self.__translate_fields = {}

        if self.settings is None:  # Only set settings if the actual index class does not define some
            self.settings = {}

        try:
            all_model_fields = [f.name for f in model._meta.get_fields() if not f.is_relation]
        except AttributeError:  # get_fields requires Django >= 1.8
            all_model_fields = [f.name for f in model._meta.local_fields]

        if isinstance(self.fields, str):
            self.fields = (self.fields,)
        elif isinstance(self.fields, (list, tuple, set)):
            self.fields = tuple(self.fields)
        else:
            raise AlgoliaIndexError('Fields must be a str, list, tuple or set')

        # Check fields
        for field in self.fields:
            # unicode is a type in python < 3.0, which we need to support (e.g. dev uses unicode_literals)
            # noinspection PyUnresolvedReferences
            if sys.version_info < (3, 0) and isinstance(field, unicode) or isinstance(field, str):
                attr = field
                name = field
            elif isinstance(field, (list, tuple)) and len(field) == 2:
                attr = field[0]
                name = field[1]
            else:
                raise AlgoliaIndexError(
                    'Invalid fields syntax: {} (type: {})'.format(field, type(field)))

            self.__translate_fields[attr] = name
            if attr in all_model_fields:
                self.__named_fields[name] = get_model_attr(attr)
            else:
                self.__named_fields[name] = check_and_get_attr(model, attr)

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
        if self.custom_objectID in chain(['pk'], all_model_fields) or hasattr(model, self.custom_objectID):
            self.objectID = get_model_attr(self.custom_objectID)
        else:
            raise AlgoliaIndexError('{} is not a model field of {}'.format(
                self.custom_objectID, model))

        # Check tags
        if self.tags:
            if self.tags in all_model_fields:
                self.tags = get_model_attr(self.tags)
            else:
                self.tags = check_and_get_attr(model, self.tags)

        # Check geo_field
        if self.geo_field:
            self.geo_field = check_and_get_attr(model, self.geo_field)

        # Check duplication_method
        if self.duplication_method:
            self.duplication_method = check_and_get_attr(model, self.duplication_method)
            if (
                not func_accepts_kwargs(self.duplication_method) and not (
                    func_supports_parameter(self.duplication_method, 'raw_record') and
                    func_supports_parameter(self.duplication_method, 'only_duplicated_ids')
                )
            ):
                raise AlgoliaIndexError(
                    '{} doesnt accept a `raw_record` or'
                    ' `only_duplicated_ids` parameter.'.format(
                    self.duplication_method
                ))
            if not self.settings.get('attributeForDistinct'):
                raise AlgoliaIndexError('Missing attributeForDistinct setting.')

        # Check should_index + get the callable or attribute/field name
        if self.should_index:
            if hasattr(model, self.should_index):
                attr = getattr(model, self.should_index)
                if type(attr) is not bool:  # if attr is a bool, we keep attr=name to getattr on instance
                    self.should_index = attr
                if callable(self.should_index):
                    self._should_index_is_method = True
            else:
                try:
                    model._meta.get_field_by_name(self.should_index)
                except:
                    raise AlgoliaIndexError('{} is not an attribute nor a field of {}.'.format(
                        self.should_index, model))

    def __init_index(self, client, model, settings):
        if not self.index_name:
            self.index_name = model.__name__

        tmp_index_name = '{index_name}_tmp'.format(index_name=self.index_name)

        if 'INDEX_PREFIX' in settings:
            self.index_name = settings['INDEX_PREFIX'] + '_' + self.index_name
            tmp_index_name = '{index_prefix}_{tmp_index_name}'.format(
                tmp_index_name=tmp_index_name,
                index_prefix=settings['INDEX_PREFIX']
            )
        if 'INDEX_SUFFIX' in settings:
            self.index_name += '_' + settings['INDEX_SUFFIX']
            tmp_index_name = '{tmp_index_name}_{index_suffix}'.format(
                tmp_index_name=tmp_index_name,
                index_suffix=settings['INDEX_SUFFIX']
            )

        self.tmp_index_name = tmp_index_name

        self.__index = client.init_index(self.index_name)
        self.__tmp_index = client.init_index(self.tmp_index_name)

    @staticmethod
    def _validate_geolocation(geolocation):
        """
        Make sure we have the proper geolocation format.
        """
        if set(geolocation) != {'lat', 'lng'}:
            raise AlgoliaIndexError(
                'Invalid geolocation format, requires "lat" and "lng" keys only got {}'.format(
                    geolocation
                )
            )

    def get_raw_record(self, instance, update_fields=None, only_duplicated_ids=None):
        """
        Gets the raw record.

        If `update_fields` is set, the raw record will be build with only
        the objectID and the given fields. Also, `_geoloc` and `_tags` will
        not be included.

        If `only_duplicated_ids` is set, it needs to be a list of duplicated data
        that was added to a record.
        """
        tmp = {'objectID': self.objectID(instance)}

        if update_fields:
            if isinstance(update_fields, str):
                update_fields = (update_fields,)

            for elt in update_fields:
                key = self.__translate_fields.get(elt, None)
                if key:
                    tmp[key] = self.__named_fields[key](instance)
        else:
            for key, value in self.__named_fields.items():
                tmp[key] = value(instance)

            if self.geo_field:
                loc = self.geo_field(instance)

                if isinstance(loc, tuple):
                    tmp['_geoloc'] = {'lat': loc[0], 'lng': loc[1]}
                elif isinstance(loc, dict):
                    self._validate_geolocation(loc)
                    tmp['_geoloc'] = loc
                elif isinstance(loc, list):
                    [self._validate_geolocation(geo) for geo in loc]
                    tmp['_geoloc'] = loc

            if self.tags:
                if callable(self.tags):
                    tmp['_tags'] = self.tags(instance)
                if not isinstance(tmp['_tags'], list):
                    tmp['_tags'] = list(tmp['_tags'])

        logger.debug('BUILD %s FROM %s', tmp['objectID'], self.model)
        if self._has_duplication_method():
            logger.debug('DUPLICATING MODEL %s', self.model)
            records = self.duplication_method(
                instance, raw_record=tmp,
                only_duplicated_ids=only_duplicated_ids
            )
            if isinstance(records, (list, tuple, types.GeneratorType)):
                return records

            # unsupported type
            raise TypeError(
                '{} should return a list, tuple or generator.'.format(
                    self.duplication_method
                )
            )

        return tmp

    def _get_duplicated_raw_records(self, *args, **kwargs):
        """
        Return a list of records, possibly duplicated if
        `_has_duplication_method()` returns True.
        It is an internal helper.
        """
        objs = self.get_raw_record(*args, **kwargs)
        return objs if self._has_duplication_method() else [objs]

    def _has_duplication_method(self):
        """Return True if this AlgoliaIndex has a duplication_method method"""
        return self.duplication_method is not None

    def _has_should_index(self):
        """Return True if this AlgoliaIndex has a should_index method or attribute"""
        return self.should_index is not None

    def _should_index(self, instance):
        """Return True if the object should be indexed (including when self.should_index is not set)."""
        if self._has_should_index():
            return self._should_really_index(instance)
        else:
            return True

    def _should_really_index(self, instance):
        """Return True if according to should_index the object should be indexed."""
        if self._should_index_is_method:
            is_method = inspect.ismethod(self.should_index)
            try:
                count_args = len(inspect.signature(self.should_index).parameters)
            except AttributeError:
                # noinspection PyDeprecation
                count_args = len(inspect.getargspec(self.should_index).args)

            if is_method or count_args == 1:
                # bound method, call with instance
                return self.should_index(instance)
            else:
                # unbound method, simply call without arguments
                return self.should_index()
        else:
            # property/attribute/Field, evaluate as bool
            attr_type = type(self.should_index)
            if attr_type is DeferredAttribute:
                attr_value = self.should_index.__get__(instance, None)
            elif attr_type is str:
                attr_value = getattr(instance, self.should_index)
            elif attr_type is property:
                attr_value = self.should_index.__get__(instance)
            else:
                raise AlgoliaIndexError('{} should be a boolean attribute or a method that returns a boolean.'.format(
                    self.should_index))
            if type(attr_value) is not bool:
                raise AlgoliaIndexError("%s's should_index (%s) should be a boolean" % (
                    instance.__class__.__name__, self.should_index))
            return attr_value

    def save_record(self, instance, update_fields=None, only_duplicated_ids=None, **kwargs):
        """Saves the record.

        If `update_fields` is set, this method will use partial_update_object()
        and will update only the given fields (never `_geoloc` and `_tags`).

        For more information about partial_update_object:
        https://github.com/algolia/algoliasearch-client-python#update-an-existing-object-in-the-index

        If `only_duplicated_ids` is set, it needs to be a list
        of duplicated data that was added to the record.
        """
        if not self._should_index(instance):
            # Should not index, but since we don't now the state of the
            # instance, we need to send a DELETE request to ensure that if
            # the instance was previously indexed, it will be removed.
            self.delete_record(instance)
            return

        try:
            if update_fields:
                index_method = self.__index.partial_update_objects
            else:
                index_method = self.__index.save_objects

            objs = self._get_duplicated_raw_records(
                instance, update_fields=update_fields,
                only_duplicated_ids=only_duplicated_ids
            )
            batch = AlgoliaIndexBatch(
                index_method, self.DEFAULT_BATCH_SIZE, objs
            )
            result = batch.flush()
            logger.info('SAVE %s FROM %s', self.objectID(instance), self.model)
            return result
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s FROM %s NOT SAVED: %s', self.objectID(instance),
                               self.model, e)

    def delete_record(self, instance, only_duplicated_ids=None):
        """Deletes the record."""
        if self._has_duplication_method():
            if only_duplicated_ids:
                object_ids = only_duplicated_ids
            else:
                object_ids = [
                    obj['objectID']
                    for obj in self.get_raw_record(instance)
                ]
        else:
            object_ids = [self.objectID(instance)]
        try:
            batch = AlgoliaIndexBatch(
                self.__index.delete_objects,
                self.DEFAULT_BATCH_SIZE, object_ids
            )
            result = batch.flush()
            logger.info('DELETE %s FROM %s', self.objectID(instance), self.model)
            return result
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s FROM %s NOT DELETED: %s', self.objectID(instance),
                               self.model, e)

    def update_records(self, qs, batch_size=DEFAULT_BATCH_SIZE, **kwargs):
        """
        Updates multiple records.

        This method is optimized for speed. It takes a QuerySet and the same
        arguments as QuerySet.update(). Optionnaly, you can specify the size
        of the batch send to Algolia with batch_size (default to 1000).

        >>> from algoliasearch_django import update_records
        >>> qs = MyModel.objects.filter(myField=False)
        >>> update_records(MyModel, qs, myField=True)
        >>> qs.update(myField=True)
        """
        if self._has_duplication_method():
            raise AlgoliaIndexError(
                'update_records() with record duplication is not supported yet'
            )

        tmp = {}
        for key, value in kwargs.items():
            name = self.__translate_fields.get(key, None)
            if name:
                tmp[name] = value

        batch = []
        objectsIDs = qs.only(self.custom_objectID).values_list(
            self.custom_objectID, flat=True)
        for elt in objectsIDs:
            tmp['objectID'] = elt
            batch.append(dict(tmp))

            if len(batch) >= batch_size:
                self.__index.partial_update_objects(batch)
                batch = []

        if len(batch) > 0:
            self.__index.partial_update_objects(batch)

    def raw_search(self, query='', params=None):
        """Performs a search query and returns the parsed JSON."""
        if params is None:
            params = {}

        try:
            return self.__index.search(query, params)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('ERROR DURING SEARCH ON %s: %s', self.index_name, e)

    def get_settings(self):
        """Returns the settings of the index."""
        try:
            logger.info('GET SETTINGS ON %s', self.index_name)
            return self.__index.get_settings()
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('ERROR DURING GET_SETTINGS ON %s: %s',
                               self.model, e)

    def set_settings(self):
        """Applies the settings to the index."""
        if not self.settings:
            return

        try:
            self.__index.set_settings(self.settings)
            logger.info('APPLY SETTINGS ON %s', self.index_name)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('SETTINGS NOT APPLIED ON %s: %s',
                               self.model, e)

    def clear_objects(self):
        """Clears all objects of an index."""
        try:
            self.__index.clear_objects()
            logger.info('CLEAR INDEX %s', self.index_name)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s NOT CLEARED: %s', self.model, e)

    def clear_index(self):
        # TODO: add deprecated warning
        self.clear_objects()

    def wait_task(self, task_id):
        try:
            self.__index.wait_task(task_id)
            logger.info('WAIT TASK %s', self.index_name)
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('%s NOT WAIT: %s', self.model, e)

    def delete(self):
        self.__index.delete()
        if self.__tmp_index:
            self.__tmp_index.delete()

    def reindex_all(self, batch_size=DEFAULT_BATCH_SIZE):
        """
        Reindex all the records.

        By default, this method use Model.objects.all() but you can implement
        a method `get_queryset` in your subclass. This can be used to optimize
        the performance (for example with select_related or prefetch_related).
        """
        should_keep_synonyms = False
        should_keep_rules = False
        try:
            if not self.settings:
                self.settings = self.get_settings()
                logger.debug('Got settings for index %s: %s', self.index_name, self.settings)
            else:
                logger.debug("index %s already has settings: %s", self.index_name, self.settings)
        except AlgoliaException as e:
            if any("Index does not exist" in arg for arg in e.args):
                pass  # Expected, let's clear and recreate from scratch
            else:
                raise e  # Unexpected error while getting settings
        try:
            if self.settings:
                replicas = self.settings.get('replicas', None)
                slaves = self.settings.get('slaves', None)

                should_keep_replicas = replicas is not None
                should_keep_slaves = slaves is not None

                if should_keep_replicas:
                    self.settings['replicas'] = []
                    logger.debug("REMOVE REPLICAS FROM SETTINGS")
                if should_keep_slaves:
                    self.settings['slaves'] = []
                    logger.debug("REMOVE SLAVES FROM SETTINGS")

                self.__tmp_index.set_settings(self.settings).wait()
                logger.debug('APPLY SETTINGS ON %s_tmp', self.index_name)
            rules = []
            synonyms = []
            for r in self.__index.browse_rules():
                rules.append(r)
            for s in self.__index.browse_synonyms():
                synonyms.append(s)
            if len(rules):
                logger.debug('Got rules for index %s: %s', self.index_name, rules)
                should_keep_rules = True
            if len(synonyms):
                logger.debug('Got synonyms for index %s: %s', self.index_name, rules)
                should_keep_synonyms = True

            self.__tmp_index.clear_objects()
            logger.debug('CLEAR INDEX %s_tmp', self.index_name)

            counts = 0
            batch = AlgoliaIndexBatch(self.__tmp_index.save_objects, batch_size)

            if hasattr(self, 'get_queryset'):
                qs = self.get_queryset()
            else:
                qs = self.model.objects.all()

            for instance in qs:
                if not self._should_index(instance):
                    continue  # should not index


                objs = self._get_duplicated_raw_records(instance)
                batch.add(objs)
                counts += 1

            logger.info('SAVE %d OBJECTS TO %s_tmp', len(batch),
                        self.index_name)
            batch.flush()

            self.__client.move_index(self.tmp_index_name,
                                     self.index_name)
            logger.info('MOVE INDEX %s_tmp TO %s', self.index_name,
                        self.index_name)

            if self.settings:
                if should_keep_replicas:
                    self.settings['replicas'] = replicas
                    logger.debug("RESTORE REPLICAS")
                if should_keep_slaves:
                    self.settings['slaves'] = slaves
                    logger.debug("RESTORE SLAVES")
                if should_keep_replicas or should_keep_slaves:
                    self.__index.set_settings(self.settings)
                if should_keep_rules:
                    response = self.__index.save_rules(rules, {'forwardToReplicas': True})
                    response.wait()
                    logger.info("Saved rules for index %s with response: {}".format(response), self.index_name)
                if should_keep_synonyms:
                    response = self.__index.save_synonyms(synonyms, {'forwardToReplicas': True})
                    response.wait()
                    logger.info("Saved synonyms for index %s with response: {}".format(response), self.index_name)
            return counts
        except AlgoliaException as e:
            if DEBUG:
                raise e
            else:
                logger.warning('ERROR DURING REINDEXING %s: %s', self.model,
                               e)


class AlgoliaIndexBatch(object):
    """Helper to construct batches of requests and send them."""

    def __init__(self, method, size, queue=None):
        """
        Initialize the batch.

        :param method:       the method used to flush the batch
        :param size:         the batch size
        :param queue:        optional queue to initialize the batch
        """
        self.method = method
        self.size = size
        # casting the queue to a list here
        self._queue = list(queue) if queue else []

    def __len__(self):
        """Return the length of the batch."""
        return len(self._queue)

    def add(self, objs):
        """Add objects to the batch."""
        self._queue.extend(objs)

    def flush(self):
        """
        Flush the batch, i.e. perform the requests, by ensuring that
        each batched request doesn't contain more than `self.size` operations.
        """
        results = []
        while self._queue:
            results.append(self.method(self._queue[:self.size]))
            self._queue = self._queue[self.size:]

        return results
