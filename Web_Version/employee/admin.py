from django.contrib import admin

# Register your models here.

from .models import Department, Designation, Employee

admin.site.register(Department)
admin.site.register(Designation)
admin.site.register(Employee)
