"""
Janeway Management command for sending preprint article and metadata to Merritt
"""

from django.core.management.base import BaseCommand
from repository import models
from plugins.merritt.models import RepoMerrittSettings, MerrittQueue
from utils.logger import get_logger
from django.utils import timezone


BATCH_SIZE = 100 
logger = get_logger(__name__)

class Command(BaseCommand):
    help = "Scan for new or updated preprint item to send to Merritt"


    def handle(self, *args, **options):
        self.stdout.write("Called handle")

        # when was the last scan? - save in the setting table
        rsettings = RepoMerrittSettings.objects.all()
        for rsetting in rsettings:
            # scan date tracks the date updated processed
            if rsetting.scan_date is None:
                pps = models.Preprint.objects.filter(repository = rsetting.repo, stage = 'preprint_published', date_updated__isnull=False).order_by("date_updated").values_list('id', 'date_updated')[:BATCH_SIZE]
            else:
                # find all the preprints where updated date is greater than that scan date
                pps = models.Preprint.objects.filter(repository = rsetting.repo, stage = 'preprint_published', date_updated__isnull=False, date_updated__gte = rsetting.scan_date).order_by("date_updated").values_list('id', 'date_updated')[:BATCH_SIZE]
            
            # update scan date for future
            scan_date = self.QueueItems(pps)
            if scan_date:
                rsetting.scan_date = scan_date
            rsetting.save()


    def QueueItems(self, pps):
        scan_date = None
        for item in pps:
            preprint_id = item[0]
            date_updated = item[1]
            # create or get queue item
            qitem = MerrittQueue.objects.get_or_create(preprint_id = preprint_id, defaults={'queue_date':timezone.now() })[0]
            # skip if this has been tried and not updated since then
            if qitem.status == MerrittQueue.ItemStatus.WAITING or qitem.queue_date < date_updated: 
                qitem.status = MerrittQueue.ItemStatus.WAITING
                qitem.queue_date = timezone.now()
                qitem.completion_date = None
                qitem.save()
            scan_date = date_updated

        return scan_date

        