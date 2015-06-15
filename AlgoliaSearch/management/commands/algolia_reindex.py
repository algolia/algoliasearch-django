from django.core.management.base import NoArgsCommand
import AlgoliaSearch

class Command(NoArgsCommand):
    help = 'Reindex all models to Algolia'

    def handle_noargs(self, **options):
        '''Run the management command.'''
        self.stdout.write('The following models will be send to Algolia:')
        for model in AlgoliaSearch.get_registered_model():
            self.stdout.write('\t* {}\n'.format(model.__name__))
            adapter = AlgoliaSearch.get_adapter(model)
            adapter.reindex_all()
