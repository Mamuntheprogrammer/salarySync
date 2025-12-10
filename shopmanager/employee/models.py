from django.db import models

# Create your models here.

from company.models import BusinessArea

class Department(models.Model):
    business_area = models.ForeignKey(BusinessArea, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Designation(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Employee(models.Model):
    emp_code = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    business_area = models.ForeignKey(BusinessArea, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)

    join_date = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.emp_code} - {self.full_name}"
