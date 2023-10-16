from django.contrib import admin
from plugins.merritt.models import *

class RepoMerrittSettingsAdmin(admin.ModelAdmin):
    pass

admin.site.register(RepoMerrittSettings, RepoMerrittSettingsAdmin)
