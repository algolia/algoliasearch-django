from django.test import TestCase

from algoliasearch_django import AlgoliaIndex, AlgoliaEngine
from algoliasearch_django.registration import RegistrationError

from .models import Website, User


class EngineTestCase(TestCase):
    def setUp(self):
        self.engine = AlgoliaEngine()

    def test_is_register(self):
        self.engine.register(Website)
        self.assertTrue(self.engine.is_registered(Website))
        self.assertFalse(self.engine.is_registered(User))

    def test_get_adapater(self):
        self.engine.register(Website)
        self.assertEquals(AlgoliaIndex,
                          self.engine.get_adapter(Website).__class__)

    def test_get_adapter_exception(self):
        with self.assertRaises(RegistrationError):
            self.engine.get_adapter(Website)

    def test_get_adapater_from_instance(self):
        self.engine.register(Website)
        instance = Website()
        self.assertEquals(
            AlgoliaIndex,
            self.engine.get_adapter_from_instance(instance).__class__)

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
        self.assertEqual(WebsiteIndex.__name__,
                         self.engine.get_adapter(Website).__class__.__name__)

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

    # TODO: test signalling hooks and update/delete methods
