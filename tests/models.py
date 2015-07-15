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

    def location(self):
        return (self._lat, self._lng)

    def permissions(self):
        return self._permissions.split(',')


class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
