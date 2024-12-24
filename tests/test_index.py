# coding=utf-8
from django.conf import settings
from django.test import TestCase


from algoliasearch_django import AlgoliaIndex
from algoliasearch_django import algolia_engine
from algoliasearch_django.models import AlgoliaIndexError

from .models import User, Website, Example


def sanitize(hit):
    if "_highlightResult" in hit:
        hit.pop("_highlightResult")
    return hit


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = algolia_engine.client
        self.user = User(
            name="Algolia",
            username="algolia",
            bio="Milliseconds matter",
            followers_count=42001,
            following_count=42,
            _lat=123,
            _lng=-42.24,
            _permissions="read,write,admin",
        )
        self.website = Website(name="Algolia", url="https://algolia.com")

        self.contributor = User(
            name="Contributor",
            username="contributor",
            bio="Contributions matter",
            followers_count=7,
            following_count=5,
            _lat=52.0705,
            _lng=-4.3007,
            _permissions="contribute,follow",
        )

        self.example = Example(
            uid=4, name="SuperK", address="Finland", lat=63.3, lng=-32.0, is_admin=True
        )
        self.example.category = ["Shop", "Grocery"]
        self.example.locations = [
            {"lat": 10.3, "lng": -20.0},
            {"lat": 22.3, "lng": 10.0},
        ]

    def tearDown(self):
        if hasattr(self, "index"):
            self.index.delete()

    def test_default_index_name(self):
        self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
        regex = r"^test_Website_django(_ci-\d+.\d+)?$"
        try:
            self.assertRegex(self.index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(self.index.index_name, regex)

    def test_custom_index_name(self):
        class WebsiteIndex(AlgoliaIndex):
            index_name = "customName"

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        regex = r"^test_customName_django(_ci-\d+.\d+)?$"
        try:
            self.assertRegex(self.index.index_name, regex)
        except AttributeError:
            self.assertRegexpMatches(self.index.index_name, regex)

    def test_index_model_with_foreign_key_reference(self):
        self.index = AlgoliaIndex(User, self.client, settings.ALGOLIA)
        self.index.reindex_all()
        self.assertFalse("blogpost" in self.index.fields)

    def test_index_name_settings(self):
        algolia_settings = dict(settings.ALGOLIA)
        del algolia_settings["INDEX_PREFIX"]
        del algolia_settings["INDEX_SUFFIX"]

        with self.settings(ALGOLIA=algolia_settings):
            self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            regex = r"^Website$"
            try:
                self.assertRegex(self.index.index_name, regex)
            except AttributeError:
                self.assertRegexpMatches(self.index.index_name, regex)

    def test_tmp_index_name(self):
        """Test that the temporary index name should respect suffix and prefix settings"""

        algolia_settings = dict(settings.ALGOLIA)

        # With no suffix nor prefix
        del algolia_settings["INDEX_PREFIX"]
        del algolia_settings["INDEX_SUFFIX"]

        with self.settings(ALGOLIA=algolia_settings):
            self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            self.assertEqual(self.index.tmp_index_name, "Website_tmp")

        # With only a prefix
        algolia_settings["INDEX_PREFIX"] = "prefix"

        with self.settings(ALGOLIA=algolia_settings):
            self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            self.assertEqual(self.index.tmp_index_name, "prefix_Website_tmp")

        # With only a suffix
        del algolia_settings["INDEX_PREFIX"]
        algolia_settings["INDEX_SUFFIX"] = "suffix"

        with self.settings(ALGOLIA=algolia_settings):
            self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            self.assertEqual(self.index.tmp_index_name, "Website_tmp_suffix")

        # With a prefix and a suffix
        algolia_settings["INDEX_PREFIX"] = "prefix"
        algolia_settings["INDEX_SUFFIX"] = "suffix"

        with self.settings(ALGOLIA=algolia_settings):
            self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)
            self.assertEqual(self.index.tmp_index_name, "prefix_Website_tmp_suffix")

    def test_reindex_with_replicas(self):
        self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)

        class WebsiteIndex(AlgoliaIndex):
            settings = {
                "replicas": [
                    self.index.index_name + "_name_asc",  # pyright: ignore
                    self.index.index_name + "_name_desc",  # pyright: ignore
                ]
            }

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

    def test_reindex_with_should_index_boolean(self):
        Website(name="Algolia", url="https://algolia.com", is_online=True)
        self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)

        class WebsiteIndex(AlgoliaIndex):
            settings = {
                "replicas": [
                    self.index.index_name + "_name_asc",  # pyright: ignore
                    self.index.index_name + "_name_desc",  # pyright: ignore
                ]
            }
            should_index = "is_online"

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

    def test_reindex_no_settings(self):
        self.maxDiff = None

        # Given an existing index defined without settings
        class WebsiteIndex(AlgoliaIndex):
            pass

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)

        # Given some existing settings on the index
        existing_settings = self.apply_some_settings(self.index)

        # When reindexing with no settings on the instance
        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

        # Expect the former settings to be kept across reindex
        self.assertEqual(
            self.index.get_settings(),
            existing_settings,
            "An index whose model has no settings should keep its settings after reindex",
        )

    def test_reindex_with_settings(self):
        import uuid

        id = str(uuid.uuid4())
        self.maxDiff = None
        index_settings = {
            "searchableAttributes": [
                "name",
                "email",
                "company",
                "city",
                "county",
                "account_names",
                "unordered(address)",
                "state",
                "zip_code",
                "phone",
                "fax",
                "unordered(web)",
            ],
            "attributesForFaceting": ["city", "company"],
            "customRanking": ["desc(followers)"],
            "queryType": "prefixAll",
            "highlightPreTag": "<mark>",
            "ranking": [
                "asc(name)",
                "typo",
                "geo",
                "words",
                "filters",
                "proximity",
                "attribute",
                "exact",
                "custom",
            ],
            "replicas": [
                "WebsiteIndexReplica_" + id + "_name_asc",
                "WebsiteIndexReplica_" + id + "_name_desc",
            ],
            "highlightPostTag": "</mark>",
            "hitsPerPage": 15,
        }

        # Given an existing index defined with settings
        class WebsiteIndex(AlgoliaIndex):
            settings = index_settings

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)

        # Given some existing query rules on the index
        # index.__index.save_rule()  # TODO: Check query rules are kept

        # Given some existing settings on the index
        existing_settings = self.apply_some_settings(self.index)

        # When reindexing with no settings on the instance
        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

        # Expect the settings to be reset to model definition over reindex
        former_settings = existing_settings
        former_settings["hitsPerPage"] = 15

        new_settings = self.index.get_settings()

        self.assertIsNotNone(new_settings)

        if new_settings is not None:
            self.assertDictEqual(new_settings, former_settings)

    def test_reindex_with_rules(self):
        # Given an existing index defined with settings
        class WebsiteIndex(AlgoliaIndex):
            settings = {"hitsPerPage": 42}

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)

        # Given some existing query rules on the index
        rule = {
            "objectID": "my-rule",
            "condition": {"pattern": "some text", "anchoring": "is"},
            "consequence": {"params": {"hitsPerPage": 42}},
        }

        self.assertIsNotNone(self.index.index_name)

        if self.index.index_name is None:
            return

        _resp = self.client.save_rule(self.index.index_name, rule["objectID"], rule)
        self.client.wait_for_task(self.index.index_name, _resp.task_id)

        # When reindexing with no settings on the instance
        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

        rules = []
        self.client.browse_rules(
            self.index.index_name,
            lambda _resp: rules.extend([_hit.to_dict() for _hit in _resp.hits]),
        )
        self.assertEqual(len(rules), 1, "There should only be one rule")
        self.assertEqual(
            rules[0]["consequence"],
            rule["consequence"],
            "The existing rule should be kept over reindex",
        )
        self.assertEqual(
            rules[0]["objectID"],
            rule["objectID"],
            "The existing rule should be kept over reindex",
        )

    def test_reindex_with_synonyms(self):
        # Given an existing index defined with settings
        class WebsiteIndex(AlgoliaIndex):
            settings = {"hitsPerPage": 42}

        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)

        self.assertIsNotNone(self.index.index_name)

        if self.index.index_name is None:
            return

        # Given some existing synonyms on the index
        synonym = {
            "objectID": "street",
            "type": "altCorrection1",
            "word": "Street",
            "corrections": ["St"],
        }
        save_synonyms_response = self.client.save_synonyms(
            self.index.index_name, synonym_hit=[synonym]
        )
        self.client.wait_for_task(self.index.index_name, save_synonyms_response.task_id)

        # When reindexing with no settings on the instance
        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.reindex_all()

        # Expect the synonyms to be kept across reindex
        synonyms = []
        self.client.browse_synonyms(
            self.index.index_name,
            lambda _resp: synonyms.extend([sanitize(_hit.to_dict()) for _hit in _resp.hits]),
        )
        self.assertEqual(len(synonyms), 1, "There should only be one synonym")
        self.assertIn(
            synonym, synonyms, "The existing synonym should be kept over reindex"
        )

    def apply_some_settings(self, index) -> dict:
        """
        Applies a sample setting to the index.

        :param index: an AlgoliaIndex that will be updated
        :return: the new settings
        """
        # When reindexing with settings on the instance
        old_hpp = (
            index.settings["hitsPerPage"] if "hitsPerPage" in index.settings else None
        )
        index.settings["hitsPerPage"] = 42
        index.reindex_all()
        index.settings["hitsPerPage"] = old_hpp
        index_settings = index.get_settings()
        # Expect the instance's settings to be applied at reindex
        self.assertEqual(
            index_settings["hitsPerPage"],
            42,
            "An index whose model has settings should apply those at reindex",
        )
        return index_settings

    def test_custom_objectID(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = "username"

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertEqual(obj["objectID"], "algolia")

    def test_custom_objectID_property(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = "reverse_username"

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertEqual(obj["objectID"], "ailogla")

    def test_invalid_custom_objectID(self):
        class UserIndex(AlgoliaIndex):
            custom_objectID = "uid"

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_geo_fields(self):
        class UserIndex(AlgoliaIndex):
            geo_field = "location"

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertEqual(obj["_geoloc"], {"lat": 123, "lng": -42.24})

    def test_several_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = "geolocations"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.example)
        self.assertEqual(
            obj["_geoloc"],
            [
                {"lat": 10.3, "lng": -20.0},
                {"lat": 22.3, "lng": 10.0},
            ],
        )

    def test_geo_fields_already_formatted(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = "geolocations"

        self.example.locations = {"lat": 10.3, "lng": -20.0}
        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.example)
        self.assertEqual(obj["_geoloc"], {"lat": 10.3, "lng": -20.0})

    def test_none_geo_fields(self):
        class ExampleIndex(AlgoliaIndex):
            geo_field = "location"

        Example.location = lambda x: None
        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.example)
        self.assertIsNone(obj.get("_geoloc"))

    def test_invalid_geo_fields(self):
        class UserIndex(AlgoliaIndex):
            geo_field = "position"

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_tags(self):
        class UserIndex(AlgoliaIndex):
            tags = "permissions"

        self.index = UserIndex(User, self.client, settings.ALGOLIA)

        # Test the users' tag individually
        obj = self.index.get_raw_record(self.user)
        self.assertListEqual(obj["_tags"], ["read", "write", "admin"])

        obj = self.index.get_raw_record(self.contributor)
        self.assertListEqual(obj["_tags"], ["contribute", "follow"])

    def test_invalid_tags(self):
        class UserIndex(AlgoliaIndex):
            tags = "tags"

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_one_field(self):
        class UserIndex(AlgoliaIndex):
            fields = "name"

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertIn("name", obj)
        self.assertNotIn("username", obj)
        self.assertNotIn("bio", obj)
        self.assertNotIn("followers_count", obj)
        self.assertNotIn("following_count", obj)
        self.assertNotIn("_lat", obj)
        self.assertNotIn("_lng", obj)
        self.assertNotIn("_permissions", obj)
        self.assertNotIn("location", obj)
        self.assertNotIn("_geoloc", obj)
        self.assertNotIn("permissions", obj)
        self.assertNotIn("_tags", obj)
        self.assertEqual(len(obj), 2)

    def test_multiple_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ("name", "username", "bio")

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertIn("name", obj)
        self.assertIn("username", obj)
        self.assertIn("bio", obj)
        self.assertNotIn("followers_count", obj)
        self.assertNotIn("following_count", obj)
        self.assertNotIn("_lat", obj)
        self.assertNotIn("_lng", obj)
        self.assertNotIn("_permissions", obj)
        self.assertNotIn("location", obj)
        self.assertNotIn("_geoloc", obj)
        self.assertNotIn("permissions", obj)
        self.assertNotIn("_tags", obj)
        self.assertEqual(len(obj), 4)

    def test_fields_with_custom_name(self):
        # tuple syntax
        class UserIndex(AlgoliaIndex):
            fields = ("name", ("username", "login"), "bio")

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertIn("name", obj)
        self.assertNotIn("username", obj)
        self.assertIn("login", obj)
        self.assertEqual(obj["login"], "algolia")
        self.assertIn("bio", obj)
        self.assertNotIn("followers_count", obj)
        self.assertNotIn("following_count", obj)
        self.assertNotIn("_lat", obj)
        self.assertNotIn("_lng", obj)
        self.assertNotIn("_permissions", obj)
        self.assertNotIn("location", obj)
        self.assertNotIn("_geoloc", obj)
        self.assertNotIn("permissions", obj)
        self.assertNotIn("_tags", obj)
        self.assertEqual(len(obj), 4)

        # list syntax
        class UserIndex(AlgoliaIndex):
            fields = ("name", ["username", "login"], "bio")

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user)
        self.assertIn("name", obj)
        self.assertNotIn("username", obj)
        self.assertIn("login", obj)
        self.assertEqual(obj["login"], "algolia")
        self.assertIn("bio", obj)
        self.assertNotIn("followers_count", obj)
        self.assertNotIn("following_count", obj)
        self.assertNotIn("_lat", obj)
        self.assertNotIn("_lng", obj)
        self.assertNotIn("_permissions", obj)
        self.assertNotIn("location", obj)
        self.assertNotIn("_geoloc", obj)
        self.assertNotIn("permissions", obj)
        self.assertNotIn("_tags", obj)
        self.assertEqual(len(obj), 4)

    def test_invalid_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ("name", "color")

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_invalid_fields_syntax(self):
        class UserIndex(AlgoliaIndex):
            fields = {"name": "user_name"}

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_invalid_named_fields_syntax(self):
        class UserIndex(AlgoliaIndex):
            fields = ("name", {"username": "login"})

        with self.assertRaises(AlgoliaIndexError):
            UserIndex(User, self.client, settings.ALGOLIA)

    def test_get_raw_record_with_update_fields(self):
        class UserIndex(AlgoliaIndex):
            fields = ("name", "username", ["bio", "description"])

        self.index = UserIndex(User, self.client, settings.ALGOLIA)
        obj = self.index.get_raw_record(self.user, update_fields=("name", "bio"))
        self.assertIn("name", obj)
        self.assertNotIn("username", obj)
        self.assertNotIn("bio", obj)
        self.assertIn("description", obj)
        self.assertEqual(obj["description"], "Milliseconds matter")
        self.assertNotIn("followers_count", obj)
        self.assertNotIn("following_count", obj)
        self.assertNotIn("_lat", obj)
        self.assertNotIn("_lng", obj)
        self.assertNotIn("_permissions", obj)
        self.assertNotIn("location", obj)
        self.assertNotIn("_geoloc", obj)
        self.assertNotIn("permissions", obj)
        self.assertNotIn("_tags", obj)
        self.assertEqual(len(obj), 3)

    def test_should_index_method(self):
        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "has_name"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(
            self.index._should_index(self.example),
            "We should index an instance when should_index(instance) returns True",
        )

        instance_should_not = Example(name=None)
        self.assertFalse(
            self.index._should_index(instance_should_not),
            "We should not index an instance when should_index(instance) returns False",
        )

    def test_should_index_unbound(self):
        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "static_should_index"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(
            self.index._should_index(self.example),
            "We should index an instance when should_index() returns True",
        )

        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "static_should_not_index"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        instance_should_not = Example()
        self.assertFalse(
            self.index._should_index(instance_should_not),
            "We should not index an instance when should_index() returns False",
        )

    def test_should_index_attr(self):
        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "index_me"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(
            self.index._should_index(self.example),
            "We should index an instance when its should_index attr is True",
        )

        instance_should_not = Example()
        instance_should_not.index_me = False
        self.assertFalse(
            self.index._should_index(instance_should_not),
            "We should not index an instance when its should_index attr is False",
        )

        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "category"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(
            AlgoliaIndexError,
            msg="We should raise when the should_index attr is not boolean",
        ):
            self.index._should_index(self.example)

    def test_should_index_field(self):
        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "is_admin"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        self.assertTrue(
            self.index._should_index(self.example),
            "We should index an instance when its should_index field is True",
        )

        instance_should_not = Example()
        instance_should_not.is_admin = False
        self.assertFalse(
            self.index._should_index(instance_should_not),
            "We should not index an instance when its should_index field is False",
        )

        class ExampleIndex(AlgoliaIndex):
            fields = "name"
            should_index = "name"

        self.index = ExampleIndex(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(
            AlgoliaIndexError,
            msg="We should raise when the should_index field is not boolean",
        ):
            self.index._should_index(self.example)

    def test_should_index_property(self):
        class ExampleIndex1(AlgoliaIndex):
            fields = "name"
            should_index = "property_should_index"

        self.index = ExampleIndex1(Example, self.client, settings.ALGOLIA)
        self.assertTrue(
            self.index._should_index(self.example),
            "We should index an instance when its should_index property is True",
        )

        class ExampleIndex2(AlgoliaIndex):
            fields = "name"
            should_index = "property_should_not_index"

        self.index = ExampleIndex2(Example, self.client, settings.ALGOLIA)
        self.assertFalse(
            self.index._should_index(self.example),
            "We should not index an instance when its should_index property is False",
        )

        class ExampleIndex3(AlgoliaIndex):
            fields = "name"
            should_index = "property_string"

        self.index = ExampleIndex3(Example, self.client, settings.ALGOLIA)
        with self.assertRaises(
            AlgoliaIndexError,
            msg="We should raise when the should_index property is not boolean",
        ):
            self.index._should_index(self.example)

    def test_save_record_should_index_boolean(self):
        self.index = AlgoliaIndex(Website, self.client, settings.ALGOLIA)

        class WebsiteIndex(AlgoliaIndex):
            custom_objectID = "name"
            settings = {
                "replicas": [
                    self.index.index_name + "_name_asc",  # pyright: ignore
                    self.index.index_name + "_name_desc",  # pyright: ignore
                ]
            }
            should_index = "is_online"

        self.website.is_online = True
        self.index = WebsiteIndex(Website, self.client, settings.ALGOLIA)
        self.index.save_record(self.website)

    def test_cyrillic(self):
        class CyrillicIndex(AlgoliaIndex):
            fields = ["bio", "name"]
            settings = {
                "searchableAttributes": ["name", "bio"],
            }
            index_name = "test_cyrillic"

        self.user.bio = "крупнейших"
        self.user.save()
        self.index = CyrillicIndex(User, self.client, settings.ALGOLIA)
        self.index.save_record(self.user)
        result = self.index.raw_search("крупнейших")
        self.assertIsNotNone(result)

        if result is not None:
            self.assertEqual(result["nbHits"], 1, "Search should return one result")
            self.assertEqual(
                result["hits"][0]["name"], "Algolia", "The result should be self.user"
            )
