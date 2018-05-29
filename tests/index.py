from algoliasearch_django import register
from algoliasearch_django.models import AlgoliaIndex
from algoliasearch_django.decorators import register as register_decorator

from .models import User, Website


@register_decorator(User)
class UserIndex(AlgoliaIndex):
    pass


class WebsiteIndex(AlgoliaIndex):
    pass


register(Website, WebsiteIndex)
