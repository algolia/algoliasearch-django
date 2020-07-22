from __future__ import unicode_literals

import inspect
from functools import partial
from itertools import chain
import logging
import sys

from django.db.models.query_utils import DeferredAttribute

from .base import BaseAlgoliaIndex, AlgoliaIndexError


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


class AlgoliaIndex(BaseAlgoliaIndex):
    """An index in the Algolia backend."""

    # Use to specify a custom field that will be used for the objectID.
    # This field should be unique.
    custom_objectID = 'pk'

    # Name of the attribute to check on instances if should_index is not a callable
    _should_index_is_method = False

    def __init__(self, model, client, settings):
        """Initializes the index."""
        if not self.index_name:
            self.index_name = model.__name__

        self._init_index(client, settings)

        super().__init__(client, settings)

        self.model = model

        all_model_fields = [f.name for f in model._meta.get_fields() if not f.is_relation]

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
                    'Invalid fields syntax: {} (type: {})'.format(field, type(field)))

            self._translate_fields[attr] = name
            if attr in all_model_fields:
                self._named_fields[name] = get_model_attr(attr)
            else:
                self._named_fields[name] = check_and_get_attr(model, attr)

        # If no fields are specified, index all the fields of the model
        if not self.fields:
            self.fields = set(all_model_fields)
            for elt in ('pk', 'id', 'objectID'):
                try:
                    self.fields.remove(elt)
                except KeyError:
                    continue
            self._translate_fields = dict(zip(self.fields, self.fields))
            self._named_fields = dict(zip(self.fields, map(get_model_attr,
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

    def get_queryset(self):
        return self.model.objects.all()

    def get_raw_record(self, instance, update_fields=None):
        tmp = super().get_raw_record(instance, update_fields)
        logger.debug('BUILD %s FROM %s', tmp['objectID'], self.model)
        return tmp

    def _should_really_index(self, instance):
        """Return True if according to should_index the object should be indexed."""
        if self._should_index_is_method:
            is_method = inspect.ismethod(self.should_index)
            try:
                count_args = len(inspect.signature(self.should_index).parameters)
            except AttributeError:
                # noinspection PyDeprecation
                count_args = len(inspect.getargspec(self.should_index).args)

            if is_method or count_args is 1:
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
