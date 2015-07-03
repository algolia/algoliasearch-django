from django.test import TestCase

from django.contrib.algoliasearch import AlgoliaIndex
from django.contrib.algoliasearch.registration import AlgoliaEngine
from django.contrib.algoliasearch.registration import RegistrationError

from .models import Example


class EngineTestCase(TestCase):
    def setUp(self):
        self.engine = AlgoliaEngine()

    def tearDown(self):
        try:
            self.engine.unregister(Example)
        except RegistrationError:
            pass

    def test_is_register(self):
        self.assertFalse(self.engine.is_registered(Example))
        self.engine.register(Example)
        self.assertTrue(self.engine.is_registered(Example))

    def test_get_adapater(self):
        self.engine.register(Example)
        self.assertEquals(AlgoliaIndex,
                          self.engine.get_adapter(Example).__class__)

    def test_get_adapater_from_instance(self):
        self.engine.register(Example)
        instance = Example()
        self.assertEquals(
            AlgoliaIndex,
            self.engine.get_adapter_from_instance(instance).__class__)

    def test_register(self):
        self.engine.register(Example)
        self.assertIn(Example, self.engine.get_registered_models())

    def test_register_with_custom_index(self):
        class ExampleIndex(AlgoliaIndex):
            pass

        self.engine.register(Example, ExampleIndex)
        self.assertEqual(ExampleIndex.__name__,
                         self.engine.get_adapter(Example).__class__.__name__)

    def test_register_fail(self):
        self.engine.register(Example)
        with self.assertRaises(RegistrationError):
            self.engine.register(Example)

    def test_unregister(self):
        self.engine.register(Example)
        self.engine.unregister(Example)
        self.assertNotIn(Example, self.engine.get_registered_models())

    def test_unregister_fail(self):
        with self.assertRaises(RegistrationError):
            self.engine.unregister(Example)

    # TODO: test signalling hooks and update/delete methods
