import factory

from .models import (
    Example,
    User,
    Website
)


class ExampleFactory(factory.django.DjangoModelFactory):
    uid = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'Example name-{}'.format(n))
    address = factory.Sequence(lambda n: 'Example address-{}'.format(n))
    lat = factory.Faker('latitude')
    lng = factory.Faker('longitude')

    class Meta:
        model = Example


class UserFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'User name-{}'.format(n))
    username = factory.Sequence(lambda n: 'User username-{}'.format(n))

    _lat = factory.Faker('latitude')
    _lng = factory.Faker('longitude')

    class Meta:
        model = User


class WebsiteFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Website name-{}'.format(n))
    url = factory.Faker('url')

    class Meta:
        model = Website
