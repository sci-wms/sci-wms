from django.db import models

# Create your models here.
class Node(models.Model):
    index = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    
    def dist(self, latin, lonin):
        pass
        return
    def loadCoordSchema(self):
        pass
    
    

class Cell(models.Model):
    index = models.IntegerField()
    node1 = models.IntegerField()
    node2 = models.IntegerField()
    node3 = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    
    def dist(self, latin, lonin):
        pass
        return
    def loadCoordSchema(self):
        pass
    
class Time(models.Model):
    index = models.IntegerField()
    date = models.DateTimeField()
    def loadTimeSchema(self):
        pass
    

class Level(models.Model):
    depth = models.FloatField()
    index = models.IntegerField()
    