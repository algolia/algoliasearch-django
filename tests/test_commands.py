from mock import patch, call, Mock

from django.test import TestCase
from django.utils.six import StringIO
from django.core.management import call_command

from .models import Website
from .models import User


class CommandsTestCase(TestCase):

    def test_reindex(self):
        with patch("algoliasearch_django.management.commands.algolia_reindex.reindex_all") as mock_reindex:
            call_command('algolia_reindex', stdout=StringIO())
        mock_reindex.assert_has_calls([
            call(Website, batch_size=1000),
            call(User, batch_size=1000)
        ], any_order=True)

    def test_reindex_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_reindex.reindex_all") as mock_reindex:
            call_command('algolia_reindex', stdout=StringIO(), model=['Website'])
        mock_reindex.assert_called_once_with(Website, batch_size=1000)

    def test_clearindex(self):
        with patch("algoliasearch_django.management.commands.algolia_clearindex.clear_index") as mock_clear:
            call_command('algolia_clearindex', stdout=StringIO())
        mock_clear.assert_has_calls([
            call(Website),
            call(User)
        ], any_order=True)

    def test_clearindex_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_clearindex.clear_index") as mock_clear:
            call_command(
                'algolia_clearindex',
                stdout=StringIO(),
                model=['Website']
            )
        mock_clear.assert_called_once_with(Website)

    def test_applysettings(self):
        with patch("algoliasearch_django.management.commands.algolia_applysettings.get_adapter") as mock_get_adapter:
            mock_adapter = Mock()
            mock_get_adapter.return_value = mock_adapter
            call_command('algolia_applysettings', stdout=StringIO())

        mock_get_adapter.assert_has_calls([
            call(Website),
            call(User)
        ], any_order=True)

        mock_adapter.set_settings.assert_has_calls([
            call(),
            call()
        ])

    def test_applysettings_with_args(self):
        with patch("algoliasearch_django.management.commands.algolia_applysettings.get_adapter") as mock_get_adapter:
            mock_adapter = Mock()
            mock_get_adapter.return_value = mock_adapter
            call_command('algolia_applysettings', stdout=StringIO(), model=['Website'])

        mock_get_adapter.assert_called_once_with(Website)
        mock_adapter.set_settings.assert_called_once()
