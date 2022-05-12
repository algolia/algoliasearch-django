from django.test import TestCase
from six import StringIO
from django.core.management import call_command

from algoliasearch_django import algolia_engine
from algoliasearch_django import get_adapter
from algoliasearch_django import clear_index

from .models import Website
from .models import User


class CommandsTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        user_index_name = get_adapter(User).index_name
        website_index_name = get_adapter(Website).index_name

        algolia_engine.client.init_index(user_index_name).delete()
        algolia_engine.client.init_index(website_index_name).delete()

    def setUp(self):
        # Create some records
        User.objects.create(name='James Bond', username="jb")
        User.objects.create(name='Captain America', username="captain")
        User.objects.create(name='John Snow', username="john_snow",
                            _lat=120.2, _lng=42.1)
        User.objects.create(name='Steve Jobs', username="genius",
                            followers_count=331213)

        self.out = StringIO()

    def tearDown(self):
        clear_index(Website)
        clear_index(User)

    def test_reindex(self):
        call_command('algolia_reindex', stdout=self.out)
        result = self.out.getvalue()

        regex = r'Website --> 0'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User --> 4'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_reindex_with_args(self):
        call_command('algolia_reindex', stdout=self.out, model=['Website'])
        result = self.out.getvalue()

        regex = r'Website --> \d+'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User --> \d+'
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)

    def test_clearindex(self):
        call_command('algolia_clearindex', stdout=self.out)
        result = self.out.getvalue()

        regex = r'Website'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_clearindex_with_args(self):
        call_command(
            'algolia_clearindex',
            stdout=self.out,
            model=['Website']
        )
        result = self.out.getvalue()

        regex = r'Website'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User'
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)

    def test_applysettings(self):
        call_command('algolia_applysettings', stdout=self.out)
        result = self.out.getvalue()

        regex = r'Website'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_applysettings_with_args(self):
        call_command('algolia_applysettings', stdout=self.out,
                     model=['Website'])
        result = self.out.getvalue()

        regex = r'Website'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User'
        try:
            self.assertNotRegex(result, regex)
        except AttributeError:
            self.assertNotRegexpMatches(result, regex)
