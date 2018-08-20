try:
    # ContextDecorator was introduced in Python 3.2
    from contextlib import ContextDecorator
except ImportError:
    ContextDecorator = None
from functools import WRAPPER_ASSIGNMENTS, wraps

from django.db.models.signals import post_save, pre_delete

from . import algolia_engine


def available_attrs(fn):
    """
    Return the list of functools-wrappable attributes on a callable.
    This was required as a workaround for http://bugs.python.org/issue3445
    under Python 2.
    """
    return WRAPPER_ASSIGNMENTS


if ContextDecorator is None:
    # ContextDecorator was introduced in Python 3.2
    # See https://docs.python.org/3/library/contextlib.html#contextlib.ContextDecorator
    class ContextDecorator:
        """
        A base class that enables a context manager to also be used as a decorator.
        """
        def __call__(self, func):
            @wraps(func, assigned=available_attrs(func))
            def inner(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return inner


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


class disable_auto_indexing(ContextDecorator):
    """
    A context decorator to disable the auto-indexing behaviour of the AlgoliaIndex

    Can be used either as a context manager or a method decorator:
    >>> with disable_auto_indexing():
    >>>     my_object.save()

    >>> @disable_auto_indexing()
    >>> big_operation()
    """

    def __init__(self, model=None):
        if model is not None:
            self.models = [model]
        else:
            self.models = algolia_engine._AlgoliaEngine__registered_models

    def __enter__(self):
        for model in self.models:
            post_save.disconnect(
                algolia_engine._AlgoliaEngine__post_save_receiver,
                sender=model
            )
            pre_delete.disconnect(
                algolia_engine._AlgoliaEngine__pre_delete_receiver,
                sender=model
            )

    def __exit__(self, exc_type, exc_value, traceback):
        for model in self.models:
            post_save.connect(
                algolia_engine._AlgoliaEngine__post_save_receiver,
                sender=model
            )
            pre_delete.connect(
                algolia_engine._AlgoliaEngine__pre_delete_receiver,
                sender=model
            )
