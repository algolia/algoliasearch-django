from django.core.management.base import BaseCommand
import AlgoliaSearch

class Command(BaseCommand):
    help = 'Reindex all models to Algolia'

    def add_arguments(self, parser):
        parser.add_argument('--batchsize', nargs='?', default=1000, type=int)
        parser.add_argument('--index', nargs='+', type=str)

    def handle(self, *args, **options):
        '''Run the management command.'''
        self.stdout.write('The following models were reindexed:')
        for model in AlgoliaSearch.get_registered_model():
            adapter = AlgoliaSearch.get_adapter(model)
            if not (options['index'] and (adapter.__class__.__name__ in options['index'])):
                continue

            counts = adapter.reindex_all(batch_size=options['batchsize'])
            self.stdout.write('\t* {} --> {}'.format(model.__name__, counts))
