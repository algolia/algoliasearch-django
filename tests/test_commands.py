from mock import patch, call, Mock, MagicMock

from django.test import TestCase
from six import StringIO
from django.core.management import call_command

from .models import Website
from .models import User


class CommandsTestCase(TestCase):

    def setUp(self):
        self.mock_website_adapter = MagicMock()
        self.mock_website_adapter.index_name = "Website"
        self.mock_example_adapter = MagicMock()
        self.mock_example_adapter.index_name = "Example"

    def test_reindex(self):
        with patch("algoliasearch_django.management.commands.algolia_reindex.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command('algolia_reindex', stdout=StringIO())
        self.mock_website_adapter.reindex_all.assert_called_once_with(batch_size=1000)
        self.mock_example_adapter.reindex_all.assert_called_once_with(batch_size=1000)

    def test_reindex_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_reindex.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command('algolia_reindex', stdout=StringIO(), index=['Website'])
        self.mock_website_adapter.reindex_all.assert_called_once_with(batch_size=1000)
        self.mock_example_adapter.reindex_all.assert_not_called()

    def test_clearindex(self):
        with patch("algoliasearch_django.management.commands.algolia_clearindex.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command('algolia_clearindex', stdout=StringIO())
        self.mock_website_adapter.clear_index.assert_called_once()
        self.mock_example_adapter.clear_index.assert_called_once()

    def test_clearindex_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_clearindex.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command(
                'algolia_clearindex',
                stdout=StringIO(),
                index=['Website']
            )
        self.mock_website_adapter.clear_index.assert_called_once()
        self.mock_example_adapter.clear_index.assert_not_called()

    def test_applysettings(self):
        with patch("algoliasearch_django.management.commands.algolia_applysettings.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command('algolia_applysettings', stdout=StringIO())
        self.mock_website_adapter.set_settings.assert_called_once()
        self.mock_example_adapter.set_settings.assert_called_once()

    def test_applysettings_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_applysettings.get_registered_adapters") as mock_iter:
            mock_iter.return_value.__iter__.return_value  = [self.mock_website_adapter, self.mock_example_adapter]
            call_command('algolia_applysettings', stdout=StringIO(), index=['Website'])
        self.mock_website_adapter.set_settings.assert_called_once()
        self.mock_example_adapter.set_settings.assert_not_called()
