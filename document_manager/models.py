from django.db import models
from django_countries.fields import CountryField


def document_upload_to(instance, filename):
    return f'documents/{instance.country}/{instance.category}/{filename}'


class Document(models.Model):

    country = models.CharField(max_length=200, choices=CountryField().choices)
    category = models.CharField(max_length=250)
    document = models.FileField(upload_to=document_upload_to)

    def __str__(self) -> str:
        return f"{self.country} - {self.category} - {self.document.name}"