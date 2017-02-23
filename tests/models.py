from django.db import models


class Example(models.Model):
    uid = models.IntegerField()
    name = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    category = []
    locations = []
    index_me = True

    def location(self):
        return (self.lat, self.lng)

    def geolocations(self):
        return self.locations

    def has_name(self):
        return self.name is not None
