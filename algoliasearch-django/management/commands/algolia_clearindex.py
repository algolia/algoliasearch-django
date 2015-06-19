from django.core.management.base import BaseCommand
import django.contrib.algoliasearch


class Command(BaseCommand):
    help = 'Clear index.'

    def add_arguments(self, parser):
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        '''Run the management command.'''
        self.stdout.write('Clear index:')
        for model in AlgoliaSearch.get_registered_model():
            adapter = AlgoliaSearch.get_adapter(model)
            if options['model'] and not (model.__name__ in options['model']):
                continue

            adapter.clear_index()
            self.stdout.write('\t* {}'.format(model.__name__))
