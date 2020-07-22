import sys

from functools import partial
from itertools import chain

from .base import BaseAlgoliaIndex, AlgoliaIndexError


def _getattr(obj, name):
    attr = getattr(obj, name, "")
    if callable(attr):
        return attr()
    else:
        return attr


def get_model_attr(name):
    return partial(_getattr, name=name)


class Aggregator(BaseAlgoliaIndex):

    custom_objectID = None

    def __init__(self, models, client, settings):
        if not self.index_name:
            self.index_name = type(self).__name__

        self._init_index(client, settings)

        super().__init__(client, settings)

        self.models = models
        all_model_fields = chain.from_iterable(
                [f.name for f in model._meta.get_fields() if not f.is_relation]
                for model in self.models)

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
            self._named_fields[name] = get_model_attr(attr)

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

        # Keep track of object model for easy faceting
        self._named_fields['_objectModel'] = self._model_name

        # Check custom_objectID
        if self.custom_objectID:
            self.custom_objectID = get_model_attr(self.custom_objectID)

        # Check tags
        if self.tags:
            self.tags = get_model_attr(self.tags)

        # Check geo_field
        if self.geo_field:
            self.geo_field = get_model_attr(self.geo_field)

        # Check should_index + get the callable or attribute/field name
        if self.should_index:
            self.should_index = get_model_attr(self.should_index)

    def _should_really_index(self, instance):
        """Return True if according to should_index the object should be indexed."""
        should_index = self.should_index(instance)
        if type(should_index) is not bool:
            raise AlgoliaIndexError("%s's should_index (%s) should be a boolean" % (
                instance.__class__.__name__, should_index))
        return should_index

    @staticmethod
    def _model_name(instance):
        return instance._meta.label

    def objectID(self, instance):
        if self.custom_objectID:
            return self.custom_objectID(instance)
        else:
            return "{}:{}".format(self._model_name(instance), instance.pk)

    def get_queryset(self):
        # This is not really a queryset, but behaves enough like one for reindex_all.
        return chain.from_iterable(model.objects.all() for model in self.models)

