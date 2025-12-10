

# Create your models here.
from django.db import models
from employee.models import Employee
from company.models import BusinessArea
from core.models import BaseModel

class LeaveType(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    yearly_quota = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class HolidayCalendar(BaseModel):
    business_area = models.ForeignKey(BusinessArea, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100)
    date = models.DateField()
    is_public_holiday = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.date} ({self.business_area})"


class EmployeeLeaveQuota(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    allocated = models.IntegerField(default=0)
    used = models.IntegerField(default=0)

    def remaining(self):
        return self.allocated - self.used


class LeaveRequest(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Leave {self.employee} ({self.start_date} - {self.end_date})"
