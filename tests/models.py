from django.db import models


class Example(models.Model):
    name = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()

    def location(self):
        return (self.lat, self.lng)
