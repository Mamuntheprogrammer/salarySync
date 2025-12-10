
# Create your models here.
from django.db import models
from employee.models import Employee
from core.models import BaseModel

class Attendance(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField(blank=True, null=True)
    
    total_work_hours = models.DurationField(blank=True, null=True)
    overtime_hours = models.DurationField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee} - {self.date}"


class BreakRecord(BaseModel):
    attendance = models.ForeignKey(Attendance, related_name='breaks', on_delete=models.CASCADE)
    break_start = models.TimeField()
    break_end = models.TimeField()

    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return f"Break for {self.attendance}"
