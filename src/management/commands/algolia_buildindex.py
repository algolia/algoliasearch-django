from django.core.management.base import BaseCommand
from django.contrib import algoliasearch


class Command(BaseCommand):
    help = 'Send all index to Algolia.'

    def add_arguments(self, parser):
        parser.add_argument('--batchsize', nargs='?', default=1000, type=int)
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        '''Run the management command.'''
        self.stdout.write('The following models were indexed:')
        for model in algoliasearch.get_registered_model():
            adapter = algoliasearch.get_adapter(model)
            if options['model'] and not (model.__name__ in options['model']):
                continue

            counts = adapter.index_all(batch_size=options['batchsize'])
            self.stdout.write('\t* {} --> {}'.format(model.__name__, counts))
