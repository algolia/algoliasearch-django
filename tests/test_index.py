from django.test import TestCase
from django.db import models

from django.contrib.algoliasearch import AlgoliaIndex
from django.contrib.algoliasearch import algolia_engine

from .models import Example


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = algolia_engine.client

    def test_default_index_name(self):
        index = AlgoliaIndex(Example, self.client)
        self.assertEqual(index.index_name, 'django_Example_test')

    def test_custom_index_name(self):
        class ExampleIndex(AlgoliaIndex):
            index_name = 'customName'

        index = ExampleIndex(Example, self.client)
        self.assertEqual(index.index_name, 'django_customName_test')
