"""
Janeway Management command for sending preprint article and metadata to Merritt
"""

from django.core.management.base import BaseCommand
from plugins.merritt.logic import PreprintToMerritt
from utils.logger import get_logger
from plugins.merritt.models import RepoMerrittSettings, MerrittQueue
from django.conf import settings as django_settings
from repository import models
import time

logger = get_logger(__name__)

class Command(BaseCommand):
    help = "Process the queue of preprint items waiting to send to Merritt"

    def check_prereq(self):
        print("checking prereq")
        if django_settings.MERRITT_URL is None:
            print("add merritt url to settings to proceed")
            return False
        if django_settings.MERRITT_USER is None:
            print("add merritt username to settings to proceed")
            return False
        if django_settings.MERRITT_KEY is None:
            print("add merritt password to settings to proceed")
            return False

    def handle(self, *args, **options):
        self.stdout.write("Called handle")
        if self.check_prereq() == False:
            return

        # get all the items from repo settings
        rsettings = RepoMerrittSettings.objects.all()
       
        # for each entry in the queue with status WAITING - process
        qitems = MerrittQueue.objects.filter(status = MerrittQueue.ItemStatus.WAITING)
        for qitem in qitems:
            preprint = models.Preprint.objects.get(pk=qitem.preprint_id)
            rsetting = rsettings.filter(repo = preprint.repository)[0]
            # call process function for the preprint item
            p = PreprintToMerritt(preprint, rsetting) 
            p.process()
            # throttle requests to Merritt
            time.sleep(30)
        