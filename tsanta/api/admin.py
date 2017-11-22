from django.contrib import admin
from api import models


admin.site.register(models.City)
admin.site.register(models.Participant)
admin.site.register(models.Group)
admin.site.register(models.Event)
admin.site.register(models.Question)
admin.site.register(models.Answer)
admin.site.register(models.Questionnaire)
admin.site.register(models.Notification)
