import time

from django.test import TestCase

from algoliasearch_django import get_adapter
from algoliasearch_django import register
from algoliasearch_django import unregister
from algoliasearch_django import raw_search

from .models import Website


class EngineTestCase(TestCase):
    def setUp(self):
        register(Website)

    def tearDown(self):
        get_adapter(Website).clear_index()
        unregister(Website)

    def test_save_signal(self):
        Website.objects.create(name='Algolia', url='https://www.algolia.com')
        Website.objects.create(name='Google', url='https://www.google.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.com')

        time.sleep(5)
        self.assertEqual(raw_search(Website)['nbHits'], 3)

    def test_delete_signal(self):
        Website.objects.create(name='Algolia', url='https://www.algolia.com')
        Website.objects.create(name='Google', url='https://www.google.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.com')

        Website.objects.get(name='Algolia').delete()
        Website.objects.get(name='Facebook').delete()

        time.sleep(5)
        result = raw_search(Website)
        self.assertEqual(result['nbHits'], 1)
        self.assertEqual(result['hits'][0]['name'], 'Google')
