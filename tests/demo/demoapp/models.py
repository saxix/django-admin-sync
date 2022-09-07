from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Base(models.Model):
    name = models.CharField(max_length=10)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name


class Detail(models.Model):
    base = models.ForeignKey(Base, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

