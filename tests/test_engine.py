import six

from django import __version__ as __django__version__
from django.conf import settings
from django.test import TestCase

from algoliasearch_django import algolia_engine, __version__
from algoliasearch_django import AlgoliaIndex
from algoliasearch_django import AlgoliaEngine
from algoliasearch_django.registration import AlgoliaEngineError
from algoliasearch_django.registration import RegistrationError

from .models import Website, User


class EngineTestCase(TestCase):
    def setUp(self):
        self.engine = AlgoliaEngine()

    def tearDown(self):
        for elt in self.engine.get_registered_models():
            self.engine.unregister(elt)

    def test_init_exception(self):
        algolia_settings = dict(settings.ALGOLIA)
        del algolia_settings["APPLICATION_ID"]
        del algolia_settings["API_KEY"]

        with self.settings(ALGOLIA=algolia_settings):
            with self.assertRaises(AlgoliaEngineError):
                AlgoliaEngine(settings=settings.ALGOLIA)

    def test_user_agent(self):
        self.assertIn(
            "Algolia for Django ({}); Django ({})".format(
                __version__, __django__version__
            ),
            self.engine.client._config._user_agent.get(),
        )

    def test_auto_discover_indexes(self):
        """Test that the `index` module was auto-discovered and the models registered"""

        six.assertCountEqual(
            self,
            [
                User,  # Registered using the `register` decorator
                Website,  # Registered using the `register` method
            ],
            algolia_engine.get_registered_models(),
        )

    def test_is_register(self):
        self.engine.register(Website)
        self.assertTrue(self.engine.is_registered(Website))
        self.assertFalse(self.engine.is_registered(User))

    def test_get_adapter(self):
        self.engine.register(Website)
        self.assertEqual(AlgoliaIndex, self.engine.get_adapter(Website).__class__)

    def test_get_adapter_exception(self):
        with self.assertRaises(RegistrationError):
            self.engine.get_adapter(Website)

    def test_get_adapter_from_instance(self):
        self.engine.register(Website)
        instance = Website()
        self.assertEqual(
            AlgoliaIndex, self.engine.get_adapter_from_instance(instance).__class__
        )

    def test_register(self):
        self.engine.register(Website)
        self.engine.register(User)
        self.assertIn(Website, self.engine.get_registered_models())
        self.assertIn(User, self.engine.get_registered_models())

    def test_register_exception(self):
        self.engine.register(Website)
        self.engine.register(User)

        with self.assertRaises(RegistrationError):
            self.engine.register(Website)

    def test_register_with_custom_index(self):
        class WebsiteIndex(AlgoliaIndex):
            pass

        self.engine.register(Website, WebsiteIndex)
        self.assertEqual(
            WebsiteIndex.__name__, self.engine.get_adapter(Website).__class__.__name__
        )

    def test_register_with_custom_index_exception(self):
        class WebsiteIndex(object):
            pass

        # WebsiteIndex is not a subclass of AlgoliaIndex
        with self.assertRaises(RegistrationError):
            self.engine.register(Website, WebsiteIndex)

    def test_unregister(self):
        self.engine.register(Website)
        self.engine.register(User)
        self.engine.unregister(Website)

        registered_models = self.engine.get_registered_models()
        self.assertNotIn(Website, registered_models)
        self.assertIn(User, registered_models)

    def test_unregister_exception(self):
        self.engine.register(User)

        with self.assertRaises(RegistrationError):
            self.engine.unregister(Website)
