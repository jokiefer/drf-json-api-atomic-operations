from django.db import models


class DJAModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = "tests"
        abstract = True


class RelatedModel(DJAModel):
    text = models.CharField(max_length=100)

    class Meta:
        ordering = ("id",)


class RelatedModelTwo(DJAModel):
    text = models.CharField(max_length=100)

    class Meta:
        ordering = ("id",)


class BasicModel(DJAModel):
    text = models.CharField(max_length=100)
    to_one = models.ForeignKey(to=RelatedModel, null=True, on_delete=models.CASCADE)
    to_many = models.ManyToManyField(to=RelatedModelTwo, null=True)

    class Meta:
        ordering = ("id",)
