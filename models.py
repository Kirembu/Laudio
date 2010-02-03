from django.db import models

# Create your models here.
class Song(models.Model):
    title = models.CharField(max_length=250)
    artist = models.CharField(max_length=150)
    album = models.CharField(max_length=150)
    genre = models.CharField(max_length=50)
    tracknumber = models.IntegerField()
    path = models.CharField(max_length=250, unique=True)
    lastmodified = models.IntegerField()
    added =  models.IntegerField()


class Playlist(models.Model):
    name = models.CharField(max_length=250)
    songs = models.ManyToManyField(Song)
    songorder = models.ManyToManyField(Song, related_name="songorder")
    added = models.IntegerField()
