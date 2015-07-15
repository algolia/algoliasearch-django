from django.db import models


class Example(models.Model):
    uid = models.IntegerField()
    name = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    category = []

    def location(self):
        return (self.lat, self.lng)


class User(models.Model):
    name = models.CharField(max_length=30)
    bio = models.CharField(max_length=140, blank=True)
    followers_count = models.BigIntegerField(default=0)
    following_count = models.BigIntegerField(default=0)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)

    def location(self):
        return (self.lat, self.lng)


class Tweet(models.Model):
    tweet_id = models.BigIntegerField(unique=True)
    user = models.ForeignKey('User')
    is_published = models.BooleanField(default=True)
    published = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=140)
    retweet = models.PositiveIntegerField(default=0)
    favori = models.PositiveIntegerField(default=0)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)

    def location(self):
        return (self.lat, self.lng)


class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
