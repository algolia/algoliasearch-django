from django.core.management.base import BaseCommand

from algoliasearch_django import get_registered_model
from algoliasearch_django import clear_objects


class Command(BaseCommand):
    help = 'Clear index.'

    def add_arguments(self, parser):
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        """Run the management command."""
        self.stdout.write('Clear index:')
        for model in get_registered_model():
            if options.get('model', None) and not (model.__name__ in
                                                   options['model']):
                continue

            clear_objects(model)
            self.stdout.write('\t* {}'.format(model.__name__))
