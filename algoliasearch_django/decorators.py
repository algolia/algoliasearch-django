def register(model):
    """
    Register the given model class and wrapped AlgoliaIndex class with the Algolia engine:

    @register(Author)
    class AuthorIndex(AlgoliaIndex):
        pass

    """
    from algoliasearch_django import AlgoliaIndex, register

    def _algolia_engine_wrapper(index_class):
        if not issubclass(index_class, AlgoliaIndex):
            raise ValueError('Wrapped class must subclass AlgoliaIndex.')

        register(model, index_class)

        return index_class
    return _algolia_engine_wrapper
