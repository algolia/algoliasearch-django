from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db.models.signals import post_save, pre_delete

from django.contrib.algoliasearch.models import AlgoliaIndex
from django.contrib.algoliasearch.version import VERSION

from algoliasearch import algoliasearch

logger = logging.getLogger(__name__)


class AlgoliaEngineError(Exception):
    '''Something went wrong with Algolia engine.'''


class RegistrationError(AlgoliaEngineError):
    '''Something went wrong when registering a model with the search sengine.'''


class AlgoliaEngine(object):
    def __init__(self, app_id=None, api_key=None):
        '''Initializes Algolia engine.'''
        params = getattr(settings, 'ALGOLIA', None)

        if not (app_id and api_key):
            if params:
                app_id = params['APPLICATION_ID']
                api_key = params['API_KEY']
            else:
                # @Deprecated: 1.1.0
                app_id = settings.ALGOLIA_APPLICATION_ID
                api_key = settings.ALGOLIA_API_KEY

        if params:
            self.auto_indexing = params.get('AUTO_INDEXING', True)

        self.__registered_models = {}
        self.client = algoliasearch.Client(app_id, api_key)
        self.client.set_extra_header('User-Agent',
                                     'Algolia for Django {}'.format(VERSION))

    def is_registered(self, model):
        '''Checks whether the given models is registered with Algolia engine.'''
        return model in self.__registered_models

    def register(self, model, index_cls=AlgoliaIndex):
        '''
        Registers the given model with Algolia engine.

        If the given model is already registered with Algolia engine, a
        RegistrationError will be raised.
        '''
        # Check for existing registration
        if self.is_registered(model):
            raise RegistrationError(
                '{} is already registered with Algolia engine'.format(model))
        # Perform the registration.
        index_obj = index_cls(model, self.client)
        self.__registered_models[model] = index_obj

        if self.auto_indexing:
            # Connect to the signalling framework.
            post_save.connect(self.__post_save_receiver, model)
            pre_delete.connect(self.__pre_delete_receiver, model)
            logger.info('REGISTER %s', model)

    def unregister(self, model):
        '''
        Unregisters the given model with Algolia engine.

        If the given model is not registered with Algolia engine, a
        RegistrationError will be raised.
        '''
        if not self.is_registered(model):
            raise RegistrationError(
                '{} is not registered with Algolia engine'.format(model))
        # Perform the unregistration.
        del self.__registered_models[model]

        if self.auto_indexing:
            # Disconnect fron the signalling framework.
            post_save.disconnect(self.__post_save_receiver, model)
            pre_delete.disconnect(self.__pre_delete_receiver, model)
            logger.info('UNREGISTER %s', model)

    def get_registered_models(self):
        '''
        Returns a sequence of models that have been registered with Algolia
        engine.
        '''
        return list(self.__registered_models.keys())

    def get_adapter(self, model):
        '''Returns the adapter associated with the given model.'''
        if self.is_registered(model):
            return self.__registered_models[model]
        raise RegistrationError(
            '{} is not registered with Algolia engine'.format(model))

    def get_adapter_from_instance(self, instance):
        model = instance.__class__
        return self.get_adapter(model)

    def update_obj_index(self, obj):
        adapter = self.get_adapter_from_instance(obj)
        adapter.update_obj_index(obj)

    def delete_obj_index(self, obj):
        adapter = self.get_adapter_from_instance(obj)
        adapter.delete_obj_index(obj)

    def raw_search(self, model, query='', params={}):
        '''Return the raw JSON.'''
        adapter = self.get_adapter(model)
        return adapter.raw_search(query, params)

    # Signalling hooks.

    def __post_save_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been saved.'''
        logger.debug('RECEIVE post_save FOR %s', instance.__class__)
        self.update_obj_index(instance)

    def __pre_delete_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been deleted.'''
        logger.debug('RECEIVE pre_delete FOR %s', instance.__class__)
        self.delete_obj_index(instance)

# Algolia engine
algolia_engine = AlgoliaEngine()
