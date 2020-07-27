import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from algoliasearch.search_client import SearchClient, SearchConfig

from .models import AlgoliaIndex, Aggregator
from .settings import SETTINGS
from .version import VERSION
from algoliasearch.version import VERSION as CLIENT_VERSION
from platform import python_version
from django import get_version as django_version

logger = logging.getLogger(__name__)


class AlgoliaEngineError(Exception):
    """Something went wrong with Algolia Engine."""


class RegistrationError(AlgoliaEngineError):
    """Something went wrong when registering a model."""


class AlgoliaEngine:
    def __init__(self, settings=SETTINGS):
        """Initializes the Algolia engine."""

        try:
            app_id = settings['APPLICATION_ID']
            api_key = settings['API_KEY']
        except KeyError:
            raise AlgoliaEngineError(
                'APPLICATION_ID and API_KEY must be defined.')

        self.__auto_indexing = settings.get('AUTO_INDEXING', True)
        self.__settings = settings

        self.__registered_models = {}
        self.__registered_adapters = []

        config = SearchConfig(app_id, api_key)
        config.headers['User-Agent'] = 'Algolia for Python (%s); Python (%s); Algolia for Django (%s); Django (%s)' \
                                       % (CLIENT_VERSION, python_version(), VERSION, django_version)
        self.client = SearchClient.create_with_config(config)

    def is_registered(self, model):
        """Checks whether the given models is registered with Algolia engine"""
        return model in self.__registered_models

    def register(self, model, index_cls=AlgoliaIndex, auto_indexing=None):
        """
        Registers the given model with Algolia engine.

        If the given model is already registered with Algolia engine, a
        RegistrationError will be raised.
        """
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
        self.__registered_adapters.append(index_obj)

        if (isinstance(auto_indexing, bool) and
                auto_indexing) or self.__auto_indexing:
            # Connect to the signalling framework.
            post_save.connect(self.__post_save_receiver, model)
            pre_delete.connect(self.__pre_delete_receiver, model)
            logger.info('REGISTER %s', model)

    def register_aggregator(self, models, index_cls=Aggregator, auto_indexing=None):
        for model in models:
            # Check for existing registration.
            if self.is_registered(model):
                raise RegistrationError(
                    '{} is already registered with Algolia engine'.format(model))

        # Perform the registration.
        if not issubclass(index_cls, Aggregator):
            raise RegistrationError(
                '{} should be a subclass of Aggregator'.format(index_cls))

        index_obj = index_cls(models, self.client, self.__settings)
        self.__registered_adapters.append(index_obj)

        for model in models:
            self.__registered_models[model] = index_obj
            if (isinstance(auto_indexing, bool) and
                    auto_indexing) or self.__auto_indexing:
                # Connect to the signalling framework.
                post_save.connect(self.__post_save_receiver, model)
                pre_delete.connect(self.__pre_delete_receiver, model)
                logger.info('REGISTER %s', model)

    def unregister(self, model):
        """
        Unregisters the given model with Algolia engine.

        If the given model is not registered with Algolia engine, a
        RegistrationError will be raised.
        """
        if not self.is_registered(model):
            raise RegistrationError(
                '{} is not registered with Algolia engine'.format(model))
        # Perform the unregistration.
        del self.__registered_models[model]

        # Disconnect from the signalling framework.
        post_save.disconnect(self.__post_save_receiver, model)
        pre_delete.disconnect(self.__pre_delete_receiver, model)
        logger.info('UNREGISTER %s', model)

    def get_registered_models(self):
        """
        Returns a list of models that have been registered with Algolia
        engine.
        """
        return list(self.__registered_models.keys())

    def get_registered_adapters(self):
        """
        Returns a list of adapters that have been registered with Algolia
        engine.
        """
        return self.__registered_adapters

    def get_adapter(self, model):
        """Returns the adapter associated with the given model."""
        if not self.is_registered(model):
            raise RegistrationError(
                '{} is not registered with Algolia engine'.format(model))

        return self.__registered_models[model]

    def get_adapter_from_instance(self, instance):
        """Returns the adapter associated with the given instance."""
        model = instance.__class__
        return self.get_adapter(model)

    # Proxies methods.

    def save_record(self, instance, **kwargs):
        """Saves the record.

        If `update_fields` is set, this method will use partial_update_object()
        and will update only the given fields (never `_geoloc` and `_tags`).

        For more information about partial_update_object:
        https://github.com/algolia/algoliasearch-client-python#update-an-existing-object-in-the-index
        """
        adapter = self.get_adapter_from_instance(instance)
        adapter.save_record(instance, **kwargs)

    def delete_record(self, instance):
        """Deletes the record."""
        adapter = self.get_adapter_from_instance(instance)
        adapter.delete_record(instance)

    def update_records(self, model, qs, batch_size=1000, **kwargs):
        """
        Updates multiple records.

        This method is optimized for speed. It takes a QuerySet and the same
        arguments as QuerySet.update(). Optionally, you can specify the size
        of the batch send to Algolia with batch_size (default to 1000).

        >>> from algoliasearch_django import update_records
        >>> qs = MyModel.objects.filter(myField=False)
        >>> update_records(MyModel, qs, myField=True)
        >>> qs.update(myField=True)
        """
        adapter = self.get_adapter(model)
        adapter.update_records(qs, batch_size=batch_size, **kwargs)

    def raw_search(self, model, query='', request_options=None):
        """Performs a search query and returns the parsed JSON."""
        if request_options is None:
            request_options = {}

        adapter = self.get_adapter(model)
        return adapter.raw_search(query, request_options)

    def clear_objects(self, model):
        """Clears the index."""
        adapter = self.get_adapter(model)
        adapter.clear_objects()

    def reindex_all(self, model, batch_size=1000):
        """
        Reindex all the records.

        By default, this method use Model.objects.all() but you can implement
        a method `get_queryset` in your subclass. This can be used to optimize
        the performance (for example with select_related or prefetch_related).
        """
        adapter = self.get_adapter(model)
        return adapter.reindex_all(batch_size)

    def reset(self, settings=None):
        """Reinitializes the Algolia engine and its client.
        :param settings: settings to use instead of the default django.conf.settings.algolia
        """
        self.__init__(settings=settings if settings is not None else SETTINGS)

    # Signalling hooks.

    def __post_save_receiver(self, instance, **kwargs):
        """Signal handler for when a registered model has been saved."""
        logger.debug('RECEIVE post_save FOR %s', instance.__class__)
        self.save_record(instance, **kwargs)

    def __pre_delete_receiver(self, instance, **kwargs):
        """Signal handler for when a registered model has been deleted."""
        logger.debug('RECEIVE pre_delete FOR %s', instance.__class__)
        self.delete_record(instance)


# Algolia engine
algolia_engine = AlgoliaEngine()
