from django.core.management.base import BaseCommand

from algoliasearch_django import get_registered_adapters
from algoliasearch_django import get_adapter


class Command(BaseCommand):
    help = 'Apply index settings.'

    def add_arguments(self, parser):
        parser.add_argument('--index', nargs='+', type=str)

    def handle(self, *args, **options):
        """Run the management command."""
        self.stdout.write('Apply settings to index:')
        for adapter in get_registered_adapters():
            if options.get('index', None) is not None:
                if (adapter.index_name not in options['index']):
                    continue

            adapter.set_settings()
            self.stdout.write('\t* {}'.format(adapter.index_name))
