from django.db import models


class Stations(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=4)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f'{self.code} - {self.name}'


class YearlyUsage(models.Model):
    date = models.DateField()
    hour = models.PositiveBigIntegerField()
    source = models.CharField(max_length=4)
    destination = models.CharField(max_length=4)
    passengers = models.IntegerField()

    def __str__(self):
        return f'{self.date}:{self.hour}|{self.source}->{self.destination}'
