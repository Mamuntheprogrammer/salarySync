from django.contrib import admin

# Register your models here.

from .models import CompanyCode, BusinessArea
admin.site.register(CompanyCode)
admin.site.register(BusinessArea)

