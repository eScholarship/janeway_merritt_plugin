from django.db import models
from repository.models import Repository, Preprint
from django.utils.translation import gettext_lazy as _

"""
Configuration for repositor specific collection
"""
class RepoMerrittSettings(models.Model):
    repo = models.OneToOneField(Repository, on_delete=models.CASCADE)
    merritt_collection = models.CharField(max_length=30)
    scan_date = models.DateTimeField(null=True)
    def __str__(self):
        return "Merritt settings: {}".format(self.repo)

"""
Save curl requests to Merritt
"""
class PreprintMerrittRequests(models.Model):
    class SubmissionStatus(models.TextChoices):
        PREP = 'P', _('Preparing to send')
        PREP_ERROR = 'PR', _('Error before sending')
        SENT = 'S', _('Sent request')
        SEND_ERROR = 'SR', _('Error sending request')
        DONE =  'D', _('Callback with success received')
        ERROR =  'E', _('Callback with failure received')

    preprint = models.ForeignKey(Preprint, on_delete=models.SET_NULL, null=True)
    request_date = models.DateTimeField()
    request_detail = models.CharField(max_length=3000, null=True)
    response = models.CharField(max_length=3000, null=True)
    status = models.CharField(max_length=2, choices=SubmissionStatus.choices, default=SubmissionStatus.PREP)

"""
Save the callback results
"""
class MerrittJobStatus(models.Model):
    class JobStatus(models.TextChoices):
        COMPLETED = 'C', _('Job completed successfully')
        ERROR = 'E', _('Job failed')

    job_id = models.CharField(max_length=100, primary_key=True)
    preprint = models.ForeignKey(Preprint, on_delete=models.SET_NULL, null=True)
    callback_date = models.DateTimeField()
    callback_response = models.CharField(max_length=3000)
    status = models.CharField(max_length=1, choices=JobStatus.choices, default=JobStatus.ERROR)

"""
Queue for preprints to send to Merritt
"""
class MerrittQueue(models.Model):
    class ItemStatus(models.TextChoices):
        WAITING = 'W', _('Item to be processed')
        PROCESSING = 'P', _('Sending the item to Merritt')
        COMPLETED = 'C', _('Item processed successfully')
        ERROR = 'E', _('Item failed')
    preprint = models.OneToOneField(Preprint, on_delete=models.CASCADE, primary_key=True)
    queue_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True)
    status = models.CharField(max_length=1, choices=ItemStatus.choices, default=ItemStatus.WAITING)