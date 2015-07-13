from django.conf import settings

SETTINGS = settings.ALGOLIA
DEBUG = SETTINGS.get('RAISE_EXCEPTIONS', settings.DEBUG)
