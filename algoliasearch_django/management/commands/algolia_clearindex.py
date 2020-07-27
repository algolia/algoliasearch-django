from django.core.management.base import BaseCommand

from algoliasearch_django import get_registered_adapters
from algoliasearch_django import clear_objects


class Command(BaseCommand):
    help = 'Clear index.'

    def add_arguments(self, parser):
        parser.add_argument('--index', nargs='+', type=str)

    def handle(self, *args, **options):
        """Run the management command."""
        self.stdout.write('Clear index:')
        for adapter in get_registered_adapters():
            if options.get('index', None) is not None:
                if (adapter.index_name not in options['index']):
                    continue

            adapter.clear_objects()
            self.stdout.write('\t* {}'.format(adapter.index_name))
