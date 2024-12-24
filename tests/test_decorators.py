from mock import ANY, call, patch

from django.test import TestCase

from algoliasearch_django import algolia_engine
from algoliasearch_django.decorators import disable_auto_indexing

from .factories import UserFactory, WebsiteFactory
from .models import User


class DecoratorsTestCase(TestCase):
    def test_disable_auto_indexing_as_decorator_for_all(self):
        """Test that the `disable_auto_indexing` should work as a decorator for all the model"""

        @disable_auto_indexing()
        def decorated_operation():
            WebsiteFactory()
            UserFactory()

        def non_decorated_operation():
            WebsiteFactory()
            UserFactory()

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            decorated_operation()

        # The decorated method should have prevented the indexing operations
        mocked_save_record.assert_not_called()

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            non_decorated_operation()

        # The non-decorated method is not preventing the indexing operations
        # (the signal was correctly re-connected for both of the models)
        mocked_save_record.assert_has_calls(
            [
                call(
                    ANY,
                    created=True,
                    raw=False,
                    sender=ANY,
                    signal=ANY,
                    update_fields=None,
                    using=ANY,
                )
            ]
            * 2
        )

    def test_disable_auto_indexing_as_decorator_for_model(self):
        """Test that the `disable_auto_indexing` should work as a decorator for a specific model"""

        @disable_auto_indexing(model=User)
        def decorated_operation():
            WebsiteFactory()
            UserFactory()

        def non_decorated_operation():
            WebsiteFactory()
            UserFactory()

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            decorated_operation()

        # The decorated method should have prevented the indexing operation for the `User` model
        # but not for the `Website` model (we get only one call)
        mocked_save_record.assert_called_once_with(
            ANY,
            created=True,
            raw=False,
            sender=ANY,
            signal=ANY,
            update_fields=None,
            using=ANY,
        )

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            non_decorated_operation()

        # The non-decorated method is not preventing the indexing operations
        # (the signal was correctly re-connected for both of the models)
        mocked_save_record.assert_has_calls(
            [
                call(
                    ANY,
                    created=True,
                    raw=False,
                    sender=ANY,
                    signal=ANY,
                    update_fields=None,
                    using=ANY,
                )
            ]
            * 2
        )

    def test_disable_auto_indexing_as_context_manager(self):
        """Test that the `disable_auto_indexing` should work as a context manager"""

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            with disable_auto_indexing():
                WebsiteFactory()

        mocked_save_record.assert_not_called()

        with patch.object(algolia_engine, "save_record") as mocked_save_record:
            WebsiteFactory()

        mocked_save_record.assert_called_once()
