from django.core.management.base import BaseCommand

from algoliasearch_django import get_registered_adapters
from algoliasearch_django import reindex_all


class Command(BaseCommand):
    help = 'Reindex all models to Algolia'

    def add_arguments(self, parser):
        parser.add_argument('--batchsize', nargs='?', default=1000, type=int)
        parser.add_argument('--index', nargs='+', type=str)

    def handle(self, *args, **options):
        """Run the management command."""
        batch_size = options.get('batchsize', None)
        if not batch_size:
            # py34-django18: batchsize is set to None if the user don't set
            # the value, instead of not be present in the dict
            batch_size = 1000

        self.stdout.write('The following indexes were reindexed:')

        for adapter in get_registered_adapters():
            if options.get('index', None) is not None:
                if (adapter.index_name not in options['index']):
                    continue

            counts = adapter.reindex_all(batch_size=batch_size)
            self.stdout.write('\t* {} --> {}'.format(adapter.index_name, counts))
