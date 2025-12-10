from django.db import models
from core.models import BaseModel

# Create your models here.

class CompanyCode(BaseModel):
    companycode = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.companycode} - {self.name}"


class BusinessArea(BaseModel):
    company = models.ForeignKey(CompanyCode, on_delete=models.CASCADE, related_name="business_areas")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
