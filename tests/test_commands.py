from django.test import TestCase
from django.core.management import call_command

from algoliasearch_django import register
from algoliasearch_django import unregister

try:
    from StringIO import StringIO
except:
    from io import StringIO

from .models import Website, User


class CommandsTestCase(TestCase):
    def setUp(self):
        register(Website)
        register(User)
        self.output = StringIO()

    def tearDown(self):
        unregister(Website)
        unregister(User)

    def test_reindex(self):
        call_command('algolia_reindex', stdout=self.output)
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

        regex = r'Website --> \d+'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

        regex = r'User --> \d+'
        try:
            self.assertRegex(result, regex)
        except AttributeError:
            self.assertRegexpMatches(result, regex)

    def test_reindex_with_args(self):
        call_command('algolia_reindex', stdout=self.output, model=['Website'])
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

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
        call_command('algolia_clearindex', stdout=self.output)
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

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
        call_command('algolia_clearindex', stdout=self.output,
                     model=['Website'])
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

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
        call_command('algolia_applysettings', stdout=self.output)
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

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
        call_command('algolia_applysettings', stdout=self.output,
                     model=['Website'])
        self.output.seek(0)
        result = ' '.join(self.output.readlines())

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
