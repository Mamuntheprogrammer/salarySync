from django.contrib import admin

# Register your models here.
from .models import BaseModel
admin.site.register(BaseModel)
