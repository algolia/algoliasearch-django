import time

from django.test import TestCase
from mock import patch, call, ANY

from algoliasearch_django import algolia_engine, AlgoliaIndex, register, unregister
from algoliasearch_django import clear_index
from algoliasearch_django import get_adapter
from algoliasearch_django import raw_search
from algoliasearch_django import update_records
from .factories import WebsiteFactory, ExampleFactory
from .models import Website, ProxyExample


class SignalTestCase(TestCase):

    @classmethod
    def tearDownClass(cls):
        algolia_engine.client.delete_index(get_adapter(Website).index_name)

    def tearDown(self):
        clear_index(Website)

    def test_save_signal(self):
        with patch.object(algolia_engine, 'save_record') as mocked_save_record:
            websites = WebsiteFactory.create_batch(3)

        mocked_save_record.assert_has_calls(
            [
                call(
                    website,
                    created=True,
                    raw=False,
                    sender=ANY,
                    signal=ANY,
                    update_fields=None,
                    using=ANY
                )
                for website in websites
            ]
        )

    def test_delete_signal(self):
        websites = WebsiteFactory.create_batch(3)

        with patch.object(algolia_engine, 'delete_record') as mocked_delete_record:
            websites[0].delete()
            websites[1].delete()

        mocked_delete_record.assert_has_calls(
            [
                call(websites[0]),
                call(websites[1])
            ]
        )

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


class ProxyModelSignalTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ProxyModelSignalTestCase, cls).setUpClass()
        class ProxyExampleIndex(AlgoliaIndex):
            fields = ['location']
        register(ProxyExample, ProxyExampleIndex)

    @classmethod
    def tearDownClass(cls):
        algolia_engine.client.delete_index(get_adapter(ProxyExample).index_name)
        unregister(ProxyExample)

    def tearDown(self):
        clear_index(ProxyExample)

    def test_save_signal_proxy_model(self):
        with patch.object(algolia_engine, 'save_record') as mocked_save_record:
            example = ExampleFactory()

        mocked_save_record.assert_has_calls(
            [
                call(
                    example,
                    created=True,
                    raw=False,
                    sender=ANY,
                    signal=ANY,
                    update_fields=None,
                    using=ANY
                )
            ]
        )

    def test_delete_signal_proxy_model(self):
        examples = ExampleFactory.create_batch(3)
        with patch.object(algolia_engine, 'delete_record') as mocked_delete_record:
            examples[1].delete()

        mocked_delete_record.assert_has_calls(
            [
                call(examples[1]),
            ]
        )
