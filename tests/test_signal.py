import time
from mock import patch, call, ANY

from django.test import TestCase, override_settings

from algoliasearch_django import algolia_engine
from algoliasearch_django import get_adapter
from algoliasearch_django import raw_search
from algoliasearch_django import clear_objects
from algoliasearch_django import update_records

from .factories import WebsiteFactory
from .models import Website


class SignalTestCase(TestCase):

    def test_save_signal(self):
        with patch.object(algolia_engine, 'save_record') as mock_save_record:
            websites = WebsiteFactory.create_batch(3)

        mock_save_record.assert_has_calls(
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
        with patch.object(algolia_engine, 'save_record'):
            websites = WebsiteFactory.create_batch(3)

        with patch.object(algolia_engine, 'delete_record') as mock_delete_record:
            websites[0].delete()
            websites[1].delete()

        mock_delete_record.assert_has_calls(
            [
                call(websites[0]),
                call(websites[1])
            ]
        )

    def test_unregistered_save_signal(self):
        algolia_engine.unregister(Website)

        with patch.object(algolia_engine, 'save_record') as mock_save_record:
            websites = WebsiteFactory.create_batch(3)
            mock_save_record.assert_not_called()

        algolia_engine.register(Website)

    def test_unregistered_delete_signal(self):
        algolia_engine.unregister(Website)

        websites = WebsiteFactory.create_batch(3)
        with patch.object(algolia_engine, 'delete_record') as mock_delete_record:
            websites[0].delete()
            websites[1].delete()
            mock_delete_record.assert_not_called()

        algolia_engine.register(Website)
