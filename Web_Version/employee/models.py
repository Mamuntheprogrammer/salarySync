from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from leave.models import Shift

User = get_user_model()

# Create your models here.

from company.models import BusinessArea

class Department(BaseModel):
    business_area = models.ForeignKey(BusinessArea, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Designation(BaseModel):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Employee(BaseModel):
    emp_code = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    business_area = models.ForeignKey(BusinessArea, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)
    nid = models.CharField(max_length=50, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_profile")

    # NEW — Default assigned shift
    shift = models.ForeignKey(Shift,on_delete=models.SET_NULL,null=True,blank=True,related_name="employees")

    join_date = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.emp_code} - {self.full_name}"


class JobHistory(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="job_history")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for change (e.g. Promotion, Transfer)")

    def __str__(self):
        return f"History: {self.employee} ({self.start_date})"
