from django.urls import re_path
from plugins.merritt import views


urlpatterns = [
    re_path(r'^manager/$', views.merritt_manager, name='merritt_manager'),
    re_path(r'^mc/(?P<job_id>jid-\w+-\w+-\w+-\w+-\w+)$', views.merritt_callback, name='merritt_callback'),
]
