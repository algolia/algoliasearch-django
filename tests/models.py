from django.db import models


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
        return (self.lat, self.lng)

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
        return True

    @property
    def property_string(self):
        return "foo"