from django.test import TestCase
from six import StringIO
from django.core.management import call_command

from algoliasearch_django import algolia_engine
from algoliasearch_django import get_adapter
from algoliasearch_django import clear_objects

from .models import Website
from .models import User


class CommandsTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        user_index_name = get_adapter(User).index_name
        website_index_name = get_adapter(Website).index_name

        algolia_engine.client.delete_index(user_index_name)
        algolia_engine.client.delete_index(website_index_name)

    def setUp(self):
        # Create some records
        u = User(
            name="James Bond",
            username="jb",
            followers_count=0,
            following_count=0,
            _lat=0,
            _lng=0,
        )
        u.save()
        u = User(
            name="Captain America",
            username="captain",
            followers_count=0,
            following_count=0,
            _lat=0,
            _lng=0,
        )
        u.save()
        u = User(
            name="John Snow",
            username="john_snow",
            _lat=120.2,
            _lng=42.1,
            followers_count=0,
            following_count=0,
        )
        u.save()
        u = User(
            name="Steve Jobs",
            username="genius",
            followers_count=331213,
            following_count=0,
            _lat=0,
            _lng=0,
        )
        u.save()

        self.out = StringIO()

    def tearDown(self):
        clear_objects(Website)
        clear_objects(User)

    def test_reindex(self):
        call_command("algolia_reindex", stdout=self.out)
        result = self.out.getvalue()

        regex = r"Website --> 0"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User --> 4"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_reindex_with_args(self):
        call_command("algolia_reindex", stdout=self.out, model=["Website"])
        result = self.out.getvalue()

        regex = r"Website --> \d+"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User --> \d+"
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)

    def test_clearindex(self):
        call_command("algolia_clearindex", stdout=self.out)
        result = self.out.getvalue()

        regex = r"Website"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_clearindex_with_args(self):
        call_command("algolia_clearindex", stdout=self.out, model=["Website"])
        result = self.out.getvalue()

        regex = r"Website"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User"
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)

    def test_applysettings(self):
        call_command("algolia_applysettings", stdout=self.out)
        result = self.out.getvalue()

        regex = r"Website"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_applysettings_with_args(self):
        call_command("algolia_applysettings", stdout=self.out, model=["Website"])
        result = self.out.getvalue()

        regex = r"Website"
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r"User"
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)
