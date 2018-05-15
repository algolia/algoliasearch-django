import time

from django.test import TestCase

from algoliasearch_django import algolia_engine
from algoliasearch_django import get_adapter
from algoliasearch_django import register
from algoliasearch_django import unregister
from algoliasearch_django import raw_search
from algoliasearch_django import clear_index
from algoliasearch_django import update_records

from .models import Website


class SignalTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        register(Website)

    @classmethod
    def tearDownClass(cls):
        algolia_engine.client.delete_index(get_adapter(Website).index_name)
        unregister(Website)

    def tearDown(self):
        clear_index(Website)

    def test_save_signal(self):
        Website.objects.create(name='Algolia', url='https://www.algolia.com')
        Website.objects.create(name='Google', url='https://www.google.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.com')

        time.sleep(10)  # FIXME: Expose last task's ID so we can waitTask instead of sleeping
        self.assertEqual(raw_search(Website)['nbHits'], 3)

    def test_delete_signal(self):
        Website.objects.create(name='Algolia', url='https://www.algolia.com')
        Website.objects.create(name='Google', url='https://www.google.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.com')

        Website.objects.get(name='Algolia').delete()
        Website.objects.get(name='Facebook').delete()

        time.sleep(10)
        result = raw_search(Website)
        self.assertEqual(result['nbHits'], 1)
        self.assertEqual(result['hits'][0]['name'], 'Google')

    def test_update_records(self):
        Website.objects.create(name='Algolia', url='https://www.algolia.com')
        Website.objects.create(name='Google', url='https://www.google.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.com')
        Website.objects.create(name='Facebook', url='https://www.facebook.fr')
        Website.objects.create(name='Facebook', url='https://fb.com')

        qs = Website.objects.filter(name='Facebook')
        update_records(Website, qs, url='https://facebook.com')
        qs.update(url='https://facebook.com')

        time.sleep(10)
        result = raw_search(Website, 'Facebook')
        self.assertEqual(result['nbHits'], qs.count())
        for res, url in zip(result['hits'], qs.values_list('url', flat=True)):
            self.assertEqual(res['url'], url)
