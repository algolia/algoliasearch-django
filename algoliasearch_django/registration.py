from __future__ import unicode_literals
import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from algoliasearch import algoliasearch

from .models import AlgoliaIndex
from .settings import SETTINGS
from .version import VERSION

logger = logging.getLogger(__name__)


class AlgoliaEngineError(Exception):
    '''Something went wrong with Algolia Engine.'''


class RegistrationError(AlgoliaEngineError):
    '''Something went wrong when registering a model.'''


class AlgoliaEngine(object):
    def __init__(self, settings=SETTINGS):
        '''Initializes Algolia engine.'''

        try:
            app_id = settings['APPLICATION_ID']
            api_key = settings['API_KEY']
        except KeyError:
            raise AlgoliaEngineError(
                'APPLICATION_ID and API_KEY must be defined.')

        self.__auto_indexing = settings.get('AUTO_INDEXING', True)
        self.__settings = settings

        self.__registered_models = {}
        self.client = algoliasearch.Client(app_id, api_key)
        self.client.set_extra_header('User-Agent',
                                     'Algolia for Django {}'.format(VERSION))

    def is_registered(self, model):
        '''Checks whether the given models is registered with Algolia engine'''
        return model in self.__registered_models

    def register(self, model, index_cls=AlgoliaIndex, auto_indexing=None):
        '''
        Registers the given model with Algolia engine.

        If the given model is already registered with Algolia engine, a
        RegistrationError will be raised.
        '''
        # Check for existing registration.
        if self.is_registered(model):
            raise RegistrationError(
                '{} is already registered with Algolia engine'.format(model))

        # Perform the registration.
        if not issubclass(index_cls, AlgoliaIndex):
            raise RegistrationError(
                '{} should be a subclass of AlgoliaIndex'.format(index_cls))
        index_obj = index_cls(model, self.client, self.__settings)
        self.__registered_models[model] = index_obj

        if (isinstance(auto_indexing, bool) and
                auto_indexing) or self.__auto_indexing:
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
        if not self.is_registered(model):
            raise RegistrationError(
                '{} is not registered with Algolia engine'.format(model))

        return self.__registered_models[model]

    def get_adapter_from_instance(self, instance):
        model = instance.__class__
        return self.get_adapter(model)

    def save_record(self, obj, **kwargs):
        adapter = self.get_adapter_from_instance(obj)
        adapter.save_record(obj, **kwargs)

    def delete_record(self, obj):
        adapter = self.get_adapter_from_instance(obj)
        adapter.delete_record(obj)

    def raw_search(self, model, query='', params={}):
        '''Return the raw JSON.'''
        adapter = self.get_adapter(model)
        return adapter.raw_search(query, params)

    # Signalling hooks.

    def __post_save_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been saved.'''
        logger.debug('RECEIVE post_save FOR %s', instance.__class__)
        self.save_record(instance, **kwargs)

    def __pre_delete_receiver(self, instance, **kwargs):
        '''Signal handler for when a registered model has been deleted.'''
        logger.debug('RECEIVE pre_delete FOR %s', instance.__class__)
        self.delete_record(instance)

# Algolia engine
algolia_engine = AlgoliaEngine()
