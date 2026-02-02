from django.contrib import admin
from .models import Attendance, BreakRecord

admin.site.register([Attendance, BreakRecord])
