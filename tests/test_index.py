from django.test import TestCase
from django.db import models

from django.contrib.algoliasearch import AlgoliaIndex
from django.contrib.algoliasearch import algolia_engine
from django.contrib.algoliasearch.models import AlgoliaIndexError

from .models import Example


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = algolia_engine.client
        self.instance = Example(uid=4,
                                name='SuperK',
                                address='Finland',
                                lat=63.3,
                                lng=-32.0)
        self.instance.category = ['Shop', 'Grocery']

    def test_default_index_name(self):
        index = AlgoliaIndex(Example, self.client)
        regex = r'django(\d+.\d+)?_Example_test'
        try:
            self.assertRegex(index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(index.index_name, regex)

    def test_custom_index_name(self):
        class ExampleIndex(AlgoliaIndex):
            index_name = 'customName'

        index = ExampleIndex(Example, self.client)
        regex = r'django(\d+.\d+)?_customName_test'
        try:
            self.assertRegex(index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(index.index_name, regex)

    def test_custom_objectID(self):
        class ExampleIndex(AlgoliaIndex):
            custom_objectID = 'uid'

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertEqual(obj['objectID'], 4)

    def test_invalid_custom_objectID(self):
        class ExampleIndex(AlgoliaIndex):
            custom_objectID = 'uuid'

        with self.assertRaises(AlgoliaIndexError):
            index = ExampleIndex(Example, self.client)

    def test_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'location'

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertEqual(obj['_geoloc'], {'lat': 63.3, 'lng': -32.0})

    def test_invalid_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'position'

        with self.assertRaises(AlgoliaIndexError):
            index = ExampleIndex(Example, self.client)

    def test_tags(self):
        class ExampleIndex(AlgoliaIndex):
            tags = 'category'

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertListEqual(obj['_tags'], self.instance.category)

    def test_invalid_tags(self):
        class ExampleIndex(AlgoliaIndex):
            tags = 'categories'

        with self.assertRaises(AlgoliaIndexError):
            index = ExampleIndex(Example, self.client)

    def test_one_field(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertNotIn('uid', obj)
        self.assertIn('name', obj)
        self.assertNotIn('address', obj)
        self.assertNotIn('lat', obj)
        self.assertNotIn('lng', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('category', obj)
        self.assertEqual(len(obj), 2)

    def test_multiple_fields(self):
        class ExampleIndex(AlgoliaIndex):
            fields = ('name', 'address')

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertNotIn('uid', obj)
        self.assertIn('name', obj)
        self.assertIn('address', obj)
        self.assertNotIn('lat', obj)
        self.assertNotIn('lng', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('category', obj)
        self.assertEqual(len(obj), 3)

    def test_fields_with_custom_name(self):
        class ExampleIndex(AlgoliaIndex):
            fields = {
                'name': 'shopName',
                'address': 'shopAddress'
            }

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertDictContainsSubset({
            'shopName': self.instance.name,
            'shopAddress': self.instance.address
        }, obj)
        self.assertNotIn('name', obj)
        self.assertNotIn('address', obj)

    def test_invalid_fields(self):
        class ExampleIndex(AlgoliaIndex):
            fields = ('name', 'color')

        with self.assertRaises(AlgoliaIndexError):
            index = ExampleIndex(Example, self.client)
