from django.conf import settings
from django.test import TestCase

from algoliasearch_django import AlgoliaIndex
from algoliasearch_django import algolia_engine
from algoliasearch_django.models import AlgoliaIndexError

from .models import User, Website, Example


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = algolia_engine.client
        self.user = User(name='Algolia', username="algolia",
                         bio='Milliseconds matter', followers_count=42001,
                         following_count=42, _lat=123, _lng=-42.24,
                         _permissions='read,write,admin')
        self.example = Example(uid=4,
                               name='SuperK',
                               address='Finland',
                               lat=63.3,
                               lng=-32.0,
                               is_admin=True)
        self.example.category = ['Shop', 'Grocery']
        self.example.locations = [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ]

    def test_default_index_name(self):
        index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
        regex = r'^test_Website_django(_travis-\d+.\d+)?$'
        try:
            self.assertRegex(index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(index.index_name, regex)

    def test_custom_index_name(self):
        class WebsiteIndex(AlgoliaIndex):
            index_name = 'customName'

        index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        regex = r'^test_customName_django(_travis-\d+.\d+)?$'
        try:
            self.assertRegex(index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(index.index_name, regex)

    def test_index_name_settings(self):
        algolia_settings = dict(settings.ALGOLIA)
        del algolia_settings['INDEX_PREFIX']
        del algolia_settings['INDEX_SUFFIX']

        with self.settings(ALGOLIA=algolia_settings):
            index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            regex = r'^Website$'
            try:
                self.assertRegex(index.index_name, regex)
            except AttributeError:
                self.assertRegexpMatches(index.index_name, regex)

    def test_reindex_with_replicas(self):
        class WebsiteIndex(AlgoliaIndex):
            settings = {
                'replicas': [
                    'django_contact_name_asc',
                    'django_contact_name_desc'
                ]
            }

        index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        index.reindex_all()

    def test_custom_objectID(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = 'username'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertEqual(obj['objectID'], 'algolia')

    def test_invalid_custom_objectID(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = 'uid'

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_geo_fields(self):
        class UserIndex(AlgoliaIndex):
            geo_field = 'location'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertEqual(obj['_geoloc'], {'lat': 123, 'lng': -42.24})

    def test_several_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'geolocations'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.example)
        self.assertEqual(obj['_geoloc'], [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ])

    def test_geo_fields_already_formatted(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'geolocations'

        self.example.locations = {'lat': 10.3, 'lng': -20.0}
        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.example)
        self.assertEqual(obj['_geoloc'], {'lat': 10.3, 'lng': -20.0})

    def test_none_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = 'location'

        Example.location = lambda x: None
        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.example)
        self.assertIsNone(obj.get('_geoloc'))

    def test_invalid_geo_fields(self):
        class UserIndex(AlgoliaIndex):
            geo_field = 'position'

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_tags(self):
        class UserIndex(AlgoliaIndex):
            tags = 'permissions'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertListEqual(obj['_tags'], ['read', 'write', 'admin'])

    def test_invalid_tags(self):
        class UserIndex(AlgoliaIndex):
            tags = 'tags'

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_one_field(self):
        class UserIndex(AlgoliaIndex):
            fields = 'name'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertIn('name', obj)
        self.assertNotIn('username', obj)
        self.assertNotIn('bio', obj)
        self.assertNotIn('followers_count', obj)
        self.assertNotIn('following_count', obj)
        self.assertNotIn('_lat', obj)
        self.assertNotIn('_lng', obj)
        self.assertNotIn('_permissions', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('_geoloc', obj)
        self.assertNotIn('permissions', obj)
        self.assertNotIn('_tags', obj)
        self.assertEqual(len(obj), 2)

    def test_multiple_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ('name', 'username', 'bio')

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertIn('name', obj)
        self.assertIn('username', obj)
        self.assertIn('bio', obj)
        self.assertNotIn('followers_count', obj)
        self.assertNotIn('following_count', obj)
        self.assertNotIn('_lat', obj)
        self.assertNotIn('_lng', obj)
        self.assertNotIn('_permissions', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('_geoloc', obj)
        self.assertNotIn('permissions', obj)
        self.assertNotIn('_tags', obj)
        self.assertEqual(len(obj), 4)

    def test_fields_with_custom_name(self):
        # tuple syntax
        class UserIndex(AlgoliaIndex):
            fields = ('name', ('username', 'login'), 'bio')

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertIn('name', obj)
        self.assertNotIn('username', obj)
        self.assertIn('login', obj)
        self.assertEqual(obj['login'], 'algolia')
        self.assertIn('bio', obj)
        self.assertNotIn('followers_count', obj)
        self.assertNotIn('following_count', obj)
        self.assertNotIn('_lat', obj)
        self.assertNotIn('_lng', obj)
        self.assertNotIn('_permissions', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('_geoloc', obj)
        self.assertNotIn('permissions', obj)
        self.assertNotIn('_tags', obj)
        self.assertEqual(len(obj), 4)

        # list syntax
        class UserIndex(AlgoliaIndex):
            fields = ('name', ['username', 'login'], 'bio')

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user)
        self.assertIn('name', obj)
        self.assertNotIn('username', obj)
        self.assertIn('login', obj)
        self.assertEqual(obj['login'], 'algolia')
        self.assertIn('bio', obj)
        self.assertNotIn('followers_count', obj)
        self.assertNotIn('following_count', obj)
        self.assertNotIn('_lat', obj)
        self.assertNotIn('_lng', obj)
        self.assertNotIn('_permissions', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('_geoloc', obj)
        self.assertNotIn('permissions', obj)
        self.assertNotIn('_tags', obj)
        self.assertEqual(len(obj), 4)

    def test_invalid_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ('name', 'color')

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_invalid_fields_syntax(self):
        class UserIndex(AlgoliaIndex):
            fields = {'name': 'user_name'}

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_invalid_named_fields_syntax(self):
        class UserIndex(AlgoliaIndex):
            fields = ('name', {'username': 'login'})

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_get_raw_record_with_update_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ('name', 'username', ['bio', 'description'])

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.user,
                                   update_fields=('name', 'bio'))
        self.assertIn('name', obj)
        self.assertNotIn('username', obj)
        self.assertNotIn('bio', obj)
        self.assertIn('description', obj)
        self.assertEqual(obj['description'], 'Milliseconds matter')
        self.assertNotIn('followers_count', obj)
        self.assertNotIn('following_count', obj)
        self.assertNotIn('_lat', obj)
        self.assertNotIn('_lng', obj)
        self.assertNotIn('_permissions', obj)
        self.assertNotIn('location', obj)
        self.assertNotIn('_geoloc', obj)
        self.assertNotIn('permissions', obj)
        self.assertNotIn('_tags', obj)
        self.assertEqual(len(obj), 3)

    def test_should_index_method(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'has_name'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(index._should_index(self.example),
                        "We should index an instance when should_index(instance) returns True")

        instance_should_not = Example(name=None)
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when should_index(instance) returns False")

    def test_should_index_unbound(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'static_should_index'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(index._should_index(self.example),
                        "We should index an instance when should_index() returns True")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'static_should_not_index'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        instance_should_not = Example()
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when should_index() returns False")

    def test_should_index_attr(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'index_me'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(index._should_index(self.example),
                        "We should index an instance when its should_index attr is True")

        instance_should_not = Example()
        instance_should_not.index_me = False
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when its should_index attr is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'category'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index attr is not boolean"):
            index._should_index(self.example)

    def test_should_index_field(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'is_admin'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(index._should_index(self.example),
                        "We should index an instance when its should_index field is True")

        instance_should_not = Example()
        instance_should_not.is_admin = False
        self.assertFalse(index._should_index(instance_should_not),
                         "We should not index an instance when its should_index field is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'name'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index field is not boolean"):
            index._should_index(self.example)

    def test_should_index_property(self):
        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'property_should_index'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(index._should_index(self.example),
                        "We should index an instance when its should_index property is True")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'property_should_not_index'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertFalse(index._should_index(self.example),
                         "We should not index an instance when its should_index property is False")

        class ExampleIndex(AlgoliaIndex):
            fields = 'name'
            should_index = 'property_string'

        index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index property is not boolean"):
            index._should_index(self.example)
