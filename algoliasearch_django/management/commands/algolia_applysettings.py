from django.core.management.base import BaseCommand

from algoliasearch_django import get_registered_model
from algoliasearch_django import get_adapter


class Command(BaseCommand):
    help = 'Apply index settings.'

    def add_arguments(self, parser):
        parser.add_argument('--model', nargs='+', type=str)

    def handle(self, *args, **options):
        """Run the management command."""
        self.stdout.write('Apply settings to index:')
        for model in get_registered_model():
            if options.get('model', None) and not (model.__name__ in
                                                   options['model']):
                continue

            get_adapter(model).set_settings()
            self.stdout.write('\t* {}'.format(model.__name__))
