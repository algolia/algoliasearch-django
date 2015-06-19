from django.core.management.base import BaseCommand
from django.contrib import algoliasearch


class Command(BaseCommand):
    help = 'Apply index settings.'

    def add_arguments(self, parser):
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        '''Run the management command.'''
        self.stdout.write('Apply settings to index:')
        for model in algoliasearch.get_registered_model():
            adapter = algoliasearch.get_adapter(model)
            if options['model'] and not (model.__name__ in options['model']):
                continue

            adapter.set_settings()
            self.stdout.write('\t* {}'.format(model.__name__))
