from django.db import models

# Create your models here.

class CompanyCode(models.Model):
    companycode = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.companycode} - {self.name}"


class BusinessArea(models.Model):
    company = models.ForeignKey(CompanyCode, on_delete=models.CASCADE, related_name="business_areas")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
