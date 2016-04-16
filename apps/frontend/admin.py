from django.contrib import admin

# Register your models here.

from django.contrib import admin

from . import models


admin.site.register(models.Document)
admin.site.register(models.ChunkyUpload)
admin.site.register(models.TaskMethod)
admin.site.register(models.TaskRequest)
admin.site.register(models.TaskRequestLine)
admin.site.register(models.TaskResult)
