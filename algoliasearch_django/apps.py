from django.apps import AppConfig


class AlgoliaConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    name = 'algoliasearch_django'

    def ready(self):
        super().ready()
        self.module.autodiscover()
