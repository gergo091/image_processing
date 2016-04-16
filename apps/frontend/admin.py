from django.contrib import admin

# Register your models here.

from django.contrib import admin

from . import models


admin.site.register(models.Document)
admin.site.register(models.ChunkyUpload)
admin.site.register(models.DetectionMethod)
admin.site.register(models.DetectionRequest)
admin.site.register(models.DetectionRequestLine)
admin.site.register(models.DetectionResult)
