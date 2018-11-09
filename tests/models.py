from django.db import models


class User(models.Model):
    name = models.CharField(max_length=30)
    username = models.CharField(max_length=30, unique=True)
    bio = models.CharField(max_length=140, blank=True)
    followers_count = models.BigIntegerField(default=0)
    following_count = models.BigIntegerField(default=0)
    _lat = models.FloatField(default=0)
    _lng = models.FloatField(default=0)
    _permissions = models.CharField(max_length=30, blank=True)

    @property
    def reverse_username(self):
        return self.username[::-1]

    def location(self):
        return self._lat, self._lng

    def permissions(self):
        return self._permissions.split(',')


class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_online = models.BooleanField(default=False)


class Example(models.Model):
    uid = models.IntegerField()
    name = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    is_admin = models.BooleanField(default=False)
    category = []
    locations = []
    index_me = True

    def location(self):
        return self.lat, self.lng

    def geolocations(self):
        return self.locations

    def has_name(self):
        return self.name is not None

    @staticmethod
    def static_should_index():
        return True

    @staticmethod
    def static_should_not_index():
        return False

    @property
    def property_should_index(self):
        return True

    @property
    def property_should_not_index(self):
        return False

    @property
    def property_string(self):
        return "foo"

    def duplication_get_locations(self):
        return [
            {'id': '1', 'name': 'Paris'},
            {'id': '2', 'name': 'San Francisco'},
            {'id': '3', 'name': 'Berlin'}
        ]

    def duplication_get_records_per_location(self, raw_record, only_duplicated_ids=None):
        for loc in self.duplication_get_locations():
            lang_record = raw_record.copy()
            lang_record['objectID'] = '{}-{}'.format(lang_record['objectID'], loc['id'])
            lang_record['location'] = loc['name']
            if not only_duplicated_ids or lang_record['objectID'] in only_duplicated_ids:
                yield lang_record

    def duplication_get_records_per_location_wrong_type(self, **kwargs):
        return 'oups'


class BlogPost(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    text = models.TextField(default="")
