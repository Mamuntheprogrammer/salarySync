from django.contrib import admin

# Register your models here.

from .models import LeaveRequest, LeaveType, EmployeeLeaveQuota, HolidayCalendar

admin.site.register(LeaveType)
admin.site.register(EmployeeLeaveQuota)
admin.site.register(LeaveRequest)
admin.site.register(HolidayCalendar)