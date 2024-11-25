import time
from mock import patch, call, ANY

from django.test import TestCase

from algoliasearch_django import algolia_engine
from algoliasearch_django import get_adapter
from algoliasearch_django import raw_search
from algoliasearch_django import clear_objects
from algoliasearch_django import update_records

from .factories import WebsiteFactory
from .models import Website


class SignalTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        get_adapter(Website).delete()

    def tearDown(self):
        clear_objects(Website)

    def test_save_signal(self):
        with patch.object(algolia_engine, "save_record") as mocked_save_record:
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
                    using=ANY,
                )
                for website in websites
            ]
        )

    def test_delete_signal(self):
        websites = WebsiteFactory.create_batch(3)

        with patch.object(algolia_engine, "delete_record") as mocked_delete_record:
            websites[0].delete()
            websites[1].delete()

        mocked_delete_record.assert_has_calls([call(websites[0]), call(websites[1])])

    def test_update_records(self):
        Website(name="Algolia", url="https://www.algolia.com", is_online=False)
        Website(name="Google", url="https://www.google.com", is_online=False)
        Website(name="Facebook", url="https://www.facebook.com", is_online=False)
        Website(name="Facebook", url="https://www.facebook.fr", is_online=False)
        Website(name="Facebook", url="https://fb.com", is_online=False)

        qs = Website.objects.filter(name="Facebook")
        update_records(Website, qs, url="https://facebook.com")
        time.sleep(10)
        qs.update(url="https://facebook.com")

        time.sleep(10)
        result = raw_search(Website, "Facebook")
        self.assertEqual(result["nbHits"], qs.count())
        for res, url in zip(result["hits"], qs.values_list("url", flat=True)):
            self.assertEqual(res["url"], url)
