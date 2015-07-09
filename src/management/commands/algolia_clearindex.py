from django.core.management.base import BaseCommand
from django.contrib import algoliasearch


class Command(BaseCommand):
    help = 'Clear index.'

    def add_arguments(self, parser):
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        '''Run the management command.'''
        self.stdout.write('Clear index:')
        for model in algoliasearch.get_registered_model():
            adapter = algoliasearch.get_adapter(model)
            if options.get('model', None) and not (model.__name__ in
                                                   options['model']):
                continue

            adapter.clear_index()
            self.stdout.write('\t* {}'.format(model.__name__))
