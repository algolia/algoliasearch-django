from django.conf import settings
from django.test import TestCase

from algoliasearch_django import AlgoliaIndex
from algoliasearch_django import algolia_engine
from algoliasearch_django.models import AlgoliaIndexError

from .models import User
from .models import Website


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = algolia_engine.client

        self.instance = User(name='Algolia', username="algolia",
                             bio='Milliseconds matter', followers_count=42001,
                             following_count=42, _lat=123, _lng=-42.24,
                             _permissions='read,write,admin')

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

    def test_custom_objectID(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = 'username'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance)
        self.assertEqual(obj['_geoloc'], {'lat': 123, 'lng': -42.24})

    def test_invalid_geo_fields(self):
        class UserIndex(AlgoliaIndex):
            geo_field = 'position'

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_tags(self):
        class UserIndex(AlgoliaIndex):
            tags = 'permissions'

        index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance)
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
        obj = index.get_raw_record(self.instance,
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
