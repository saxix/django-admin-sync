from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Base(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(
        "self", blank=True, null=True, related_name="childs", on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name


class Extra(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Detail(models.Model):
    base = models.ForeignKey(Base, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    brother = models.OneToOneField(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )
    extra = models.OneToOneField(Extra, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
