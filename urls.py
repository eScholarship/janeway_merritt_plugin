from django.conf.urls import url
from plugins.merritt import views


urlpatterns = [
    url(r'^manager/$', views.merritt_manager, name='merritt_manager'),
    url(r'^mc/(?P<job_id>jid-\w+-\w+-\w+-\w+-\w+)$', views.merritt_callback, name='merritt_callback'),
]
