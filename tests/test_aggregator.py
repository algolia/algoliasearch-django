from mock import patch, MagicMock

from django.conf import settings
from django.test import TestCase

from algoliasearch_django import Aggregator
from algoliasearch_django import algolia_engine
from algoliasearch_django.models import AlgoliaIndexError

from .models import Website, Example, User
from .factories import WebsiteFactory, ExampleFactory, UserFactory


class AggregatorTestCase(TestCase):

    def setUp(self):
        self.algolia_client = MagicMock()

    def test_default_index_name(self):
        index = Aggregator([], self.algolia_client, settings.ALGOLIA)
        self.assertEqual(index.index_name, "test_Aggregator_django")

    def test_fields(self):
        index = Aggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        self.assertEqual(index.fields, {'name', 'url', 'is_online', 'lng', 'is_admin', 'address',  'lat', 'uid'})

    @patch.object(algolia_engine, "save_record")
    def test_object_id(self, _):
        index = Aggregator([Website], self.algolia_client, settings.ALGOLIA)
        website = WebsiteFactory()
        self.assertEqual(index.objectID(website), "tests.Website:1")

    @patch.object(algolia_engine, "save_record")
    def test_search(self, _):
        mock_results = {
            "hits": [{
                "objectID": "web.Job:951",
                "_objectModel": "web.Job"
            }]
        }
        self.algolia_client.init_index.return_value.search.return_value = mock_results

        index = Aggregator([Website], self.algolia_client, settings.ALGOLIA)
        results = index.raw_search('example')
        self.assertDictEqual(results, mock_results)

    @patch.object(algolia_engine, "save_record")
    def test_get_raw_record(self, _):
        index = Aggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        website = WebsiteFactory()
        record = index.get_raw_record(website)
        self.assertEqual(record['objectID'], "tests.Website:1")
        self.assertEqual(record['_objectModel'], "tests.Website")
        self.assertEqual(record['address'], "")

    @patch.object(algolia_engine, "save_record")
    def test_get_raw_record_explicit_fields(self, _):
        class CustomAggregator(Aggregator):
            fields = ("name", "url", "has_name", "property_string")
        index = CustomAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory(name="example")
        record = index.get_raw_record(example)
        self.assertEqual(record['objectID'], "tests.Example:1")
        self.assertEqual(record['_objectModel'], "tests.Example")
        self.assertEqual(record['property_string'], "foo")
        self.assertTrue(record['has_name'])

    @patch.object(algolia_engine, "save_record")
    def test_should_index_attr(self, _):
        class CustomAggregator(Aggregator):
            should_index = "index_me"
        index = CustomAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory()
        self.assertTrue(index._should_index(example))
        example.index_me = False
        self.assertFalse(index._should_index(example))

    @patch.object(algolia_engine, "save_record")
    def test_should_index_unbound(self, _):
        class ShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'static_should_index'

        index = ShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory()
        self.assertTrue(index._should_index(example))

        class ShouldNotIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'static_should_not_index'

        index = ShouldNotIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        self.assertFalse(index._should_index(example))

    def test_should_index_method(self):
        class ShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'has_name'

        index = ShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory()
        self.assertTrue(index._should_index(example))

        example.name = None
        self.assertFalse(index._should_index(example))

    def test_should_index_field(self):
        class ShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'is_admin'

        index = ShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory(is_admin=True)
        self.assertTrue(index._should_index(example))

        example.is_admin = False
        self.assertFalse(index._should_index(example))

        class IncorrectShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'name'

        index = IncorrectShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory(name="text")
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index field is not boolean"):
            index._should_index(example)

    def test_should_index_property(self):

        class PropertyShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'property_should_index'

        index = PropertyShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory()
        self.assertTrue(index._should_index(example))

        class PropertyShouldNotIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'property_should_not_index'

        index = PropertyShouldNotIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        self.assertFalse(index._should_index(example))

        class PropertyStringShouldIndexAggregator(Aggregator):
            fields = 'name'
            should_index = 'property_string'

        index = PropertyStringShouldIndexAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        with self.assertRaises(AlgoliaIndexError, msg="We should raise when the should_index property is not boolean"):
            index._should_index(example)

    def test_geo_fields(self):
        class CustomAggregator(Aggregator):
            geo_field = 'location'

        index = CustomAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory(lat=123, lng=-42.24)
        self.assertTrue(index._should_index(example))
        obj = index.get_raw_record(example)
        self.assertEqual(obj['_geoloc'], {'lat': 123, 'lng': -42.24})

    def test_several_geo_fields(self):
        class CustomAggregator(Aggregator):
            geo_field = 'geolocations'

        index = CustomAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)
        example = ExampleFactory()
        example.locations = [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ]
        obj = index.get_raw_record(example)
        self.assertEqual(obj['_geoloc'], [
            {'lat': 10.3, 'lng': -20.0},
            {'lat': 22.3, 'lng': 10.0},
        ])

    @patch.object(algolia_engine, "save_record")
    def test_tags(self, _):
        class CustomAggregator(Aggregator):
            tags = 'permissions'

        index = CustomAggregator([Website, Example], self.algolia_client, settings.ALGOLIA)

        # Test the users' tag individually
        user = UserFactory(_permissions='read,write,admin')
        obj = index.get_raw_record(user)
        self.assertListEqual(obj['_tags'], ['read', 'write', 'admin'])

    @patch.object(algolia_engine, "save_record")
    def test_custom_objectID(self, _):
        class CustomAggregator(Aggregator):
            custom_objectID = 'username'

        index = CustomAggregator([Website, User], self.algolia_client, settings.ALGOLIA)
        obj = index.get_raw_record(UserFactory(username="algolia"))
        self.assertEqual(obj['objectID'], 'algolia')

    @patch.object(algolia_engine, "save_record")
    def test_custom_objectID_property(self, _):
        class CustomAggregator(Aggregator):
            custom_objectID = 'reverse_username'

        index = CustomAggregator([Website, User], self.algolia_client, settings.ALGOLIA)
        obj = index.get_raw_record(UserFactory(username="algolia"))
        self.assertEqual(obj['objectID'], 'ailogla')
