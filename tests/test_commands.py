from django.test import TestCase
from django.utils.six import StringIO
from django.core.management import call_command

from algoliasearch_django import register
from algoliasearch_django import unregister

from .models import Website, User


class CommandsTestCase(TestCase):
    def setUp(self):
        register(Website)
        register(User)
        self.out = StringIO()

    def tearDown(self):
        unregister(Website)
        unregister(User)

    def test_reindex(self):
        call_command('algolia_reindex', stdout=self.out)
        result = self.out.getvalue()

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
        call_command('algolia_clearindex', stdout=self.out,
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
