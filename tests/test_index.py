from django.test import TestCase

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
                                lng=-32.0,
                                is_admin=True)
        self.instance.category = ['Shop', 'Grocery']
        self.instance.locations = [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ]

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

    def test_several_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'geolocations'

        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertEqual(obj['_geoloc'], [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ])

    def test_geo_fields_already_formatted(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'geolocations'

        self.instance.locations = {'lat': 10.3, 'lng': -20.0}
        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertEqual(obj['_geoloc'], {'lat': 10.3, 'lng': -20.0})

    def test_none_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'location'

        Example.location = lambda x: None
        index = ExampleIndex(Example, self.client)
        obj = index._build_object(self.instance)
        self.assertIsNone(obj.get('_geoloc'))

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
            ExampleIndex(Example, self.client)

    def test_should_index_method(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'has_name'

        index = ExampleIndex(Example, self.client)
        self.assertTrue(index._should_index(self.instance),
                        "We should index an instance when should_index(instance) returns True")

        instance_should_not = Example(name=None)
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when should_index(instance) returns False")

    def test_should_index_unbound(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'static_should_index'

        index = ExampleIndex(Example, self.client)
        self.assertTrue(index._should_index(self.instance),
                        "We should index an instance when should_index() returns True")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'static_should_not_index'

        index = ExampleIndex(Example, self.client)
        instance_should_not = Example()
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when should_index() returns False")

    def test_should_index_attr(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'index_me'

        index = ExampleIndex(Example, self.client)
        self.assertTrue(index._should_index(self.instance),
                        "We should index an instance when its should_index attr is True")

        instance_should_not = Example()
        instance_should_not.index_me = False
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when its should_index attr is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'category'

        index = ExampleIndex(Example, self.client)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index attr is not boolean"):
            index._should_index(self.instance)

    def test_should_index_field(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'is_admin'

        index = ExampleIndex(Example, self.client)
        self.assertTrue(index._should_index(self.instance),
                        "We should index an instance when its should_index field is True")

        instance_should_not = Example()
        instance_should_not.is_admin = False
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when its should_index field is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'name'

        index = ExampleIndex(Example, self.client)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index field is not boolean"):
            index._should_index(self.instance)

    def test_should_index_property(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'property_should_index'

        index = ExampleIndex(Example, self.client)
        self.assertTrue(index._should_index(self.instance),
                        "We should index an instance when its should_index property is True")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'static_should_not_index'

        index = ExampleIndex(Example, self.client)
        self.assertFalse(index._should_index(self.instance),
                         "We should not index an instance when its should_index property is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'property_string'

        index = ExampleIndex(Example, self.client)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index property is not boolean"):
            index._should_index(self.instance)
