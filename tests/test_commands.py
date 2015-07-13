from django.test import TestCase
from django.core.management import call_command

from algoliasearch_django import AlgoliaIndex, register, unregister

try:
    from StringIO import StringIO
except:
    from io import StringIO

from .models import Example


class CommandsTestCase(TestCase):
    def setUp(self):
        class ExampleIndex(AlgoliaIndex):
            field = 'name'

        register(Example, ExampleIndex)
        self.output = StringIO()

    def tearDown(self):
        unregister(Example)

    def test_reindex(self):
        call_command('algolia_reindex', stdout=self.output)
        self.output.seek(0)
        result = self.output.readlines()
        self.assertEqual(len(result), 2)

        regex = r'Example --> \d+'
        try:
            self.assertRegex(result[1], regex)
        except AttributeError:
            self.assertRegexpMatches(result[1], regex)

    def test_clearindex(self):
        call_command('algolia_clearindex', stdout=self.output)
        self.output.seek(0)
        result = self.output.readlines()
        self.assertEqual(len(result), 2)

        regex = r'Example'
        try:
            self.assertRegex(result[1], regex)
        except AttributeError:
            self.assertRegexpMatches(result[1], regex)

    def test_applysettings(self):
        call_command('algolia_applysettings', stdout=self.output)
        self.output.seek(0)
        result = self.output.readlines()
        self.assertEqual(len(result), 2)

        regex = r'Example'
        try:
            self.assertRegex(result[1], regex)
        except AttributeError:
            self.assertRegexpMatches(result[1], regex)
