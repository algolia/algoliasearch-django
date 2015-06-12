from __future__ import unicode_literals

import sys, json

from django.conf import settings
from django.core.signals import request_finished
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_delete
from django.utils.encoding import force_text
from django.utils.html import strip_tags
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

from AlgoliaSearch.models import SearchIndex

# TODO: clean import

class IndexAdapterError(Exception):
    '''Something went wrong with a index adapter.'''

class IndexAdapter(object):
    '''An adapater for indexing a model.'''

    # Use to specify the fields that should be included in the index.
    fields = ()

    # Use to specify the geo-fields that should be used for location search.
    geo_fields = ()

    # Use to specify the settings of the index.
    settings = ()

    def __init__(self, model):
        '''Initializes the index adapter.'''
        self.model = model
        # TODO: initializes other field


class SearchEngineError(Exception):
    '''Something went wrong with the search engine.'''

class RegistrationError(SearchEngineError):
    '''Something went wrong when registering a model with the search sengine.'''

class SearchEngine(object):
    def __init__(self):
        '''Initializes the search engine.'''
        self._registered_models = {}

    def is_registered(self, model):
        '''Checks whether the given models is registered with the search engine.'''
        return model in self._registered_model

    def register(self, model, adapter_cls=IndexAdapter):
        '''
        Registers the given model with the search engine.

        If the given model is already registered with the search engine, a
        RegistrationError will be raised.
        '''
        # Check for existing registration
        if self.is_registered(model):
            raise RegistrationError('{} is already registered with the search engine'.format(
                model
            ))
        # Perform the registration.
        adapter_obj = adapter_cls(model)
        self._registered_models[model] = adapter_obj
        # Connect to the signalling framework.
        post_save.connect(self._post_save_receiver, model)
        pre_delete.connect(self._pre_delete_receiver, model)

    def unregister(self, model):
        '''
        Unregisters the given model with the search engine.

        If the given model is not registered with the search engine, a
        RegistrationError will be raised.
        '''
        if not self.is_registered(model):
            raise RegistrationError('{} is not registered with the search engine'.format(
                model
            ))
        # Perform the unregistration.
        del self._registered_models[model]
        # Disconnect fron the signalling framework.
        post_save.disconnect(self._post_save_receiver, model)
        pre_delete.disconnect(self._pre_delete_receiver, model)

    def get_registered_model(self):
        '''Returns a sequence of models that have been registered with the search engine.'''
        return list(self._registered_models.keys())

    def get_adapter(self, model):
        '''Returns the adapter associated with the given model.'''
        if self.is_registered(model):
            return self._registered_models[model]
        raise RegistrationError('{} is not registered with the search engine'.format(
            model
        ))

    def update_obj_index(self, obj):
        # TODO: update instance
        pass

    def delete_obj_index(self, obj):
        # TODO: delete instance
        pass

    # Signalling hooks.

    def _post_save_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been saved.'''
        self.update_obj_index(instance)

    def _pre_delete_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been deleted.'''
        delete_obj_index(instance)


# The search engine
search_engine = SearchEngine()
