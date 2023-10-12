from multiprocessing import process
from wsgiref.util import request_uri
from django.shortcuts import render
from django.http import HttpResponse
from plugins.merritt import forms
from utils.logger import get_logger
from plugins.merritt.models import MerrittJobStatus, MerrittQueue, PreprintMerrittRequests
import json
from django.views.decorators.csrf import csrf_exempt
from .models import MerrittJobStatus
from django.utils import timezone

logger = get_logger(__name__)

"""
Placeholder for page for stats on Merritt submission and status
"""
def merritt_manager(request):
    form = forms.DummyManagerForm()

    template = 'merritt/manager.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


"""
Callback function called by Merritt to share result of the submission
"""
@csrf_exempt
def merritt_callback(request, job_id):
    logger.info(request)
    print("callback called for job"  + str(job_id))
    if request.method == "POST":
        data = json.loads(request.body)
        # make sure the job id in the body of the post is same as in the callback url
        if data['job:jobState']['job:jobID'] == job_id:
            process_callback(data)
            return HttpResponse(status=200)

    # make sure this is a post request
    print(request)
    return HttpResponse(status=403)

"""
Extract information from posted data and update status 
"""
def process_callback(data):
    job_id = data['job:jobState']['job:jobID']
    preprint_id = data['job:jobState']['job:localID']
    status = data['job:jobState']['job:jobStatus']
    job = MerrittJobStatus(job_id = job_id, callback_date = timezone.now(), callback_response = json.dumps(data), preprint_id=preprint_id)
    qitem = MerrittQueue.objects.get(preprint_id = preprint_id)
    ritem = PreprintMerrittRequests.objects.filter(preprint_id = preprint_id, status = PreprintMerrittRequests.SubmissionStatus.SENT).order_by('-request_date').first()
    if "COMPLETED" in status:
        job.status = MerrittJobStatus.JobStatus.COMPLETED
        qitem.status = MerrittQueue.ItemStatus.COMPLETED
        ritem.status = PreprintMerrittRequests.SubmissionStatus.DONE
    else:
        job.status = MerrittJobStatus.JobStatus.ERROR
        qitem.status = MerrittQueue.ItemStatus.ERROR
        ritem.status = PreprintMerrittRequests.SubmissionStatus.ERROR
    qitem.completion_date = timezone.now()
    job.save()
    qitem.save()
    ritem.save()
