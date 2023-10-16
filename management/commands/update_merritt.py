"""
Janeway Management command for sending a preprint article and metadata to Merritt
"""


from django.core.management.base import BaseCommand, CommandError
from plugins.merritt.logic import PreprintToMerritt
from repository import models
from plugins.merritt.models import RepoMerrittSettings
from django.conf import settings as django_settings
from utils.logger import get_logger

logger = get_logger(__name__)

class Command(BaseCommand):
    """ Takes a preprint ID and send to Merritt """
    help = "Send article to Merritt for the provided preprint ID."

    def add_arguments(self, parser):
        parser.add_argument(
            "preprint_id", help="`id` of preprint to send to Merritt", type=str
        )

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
        preprint_id = options['preprint_id']

        logger.info("Attempting to send preprint to Merritt for preprint_id=" + preprint_id)

        try:
            # get the preprint that matches the provided preprint_id
            preprint = models.Preprint.objects.get(pk=preprint_id)
        except models.Preprint.DoesNotExist:
            raise CommandError('No preprint found with preprint_id=' + preprint_id)

        # get collection for this repo
        try:
            reposetting = RepoMerrittSettings.objects.get(repo=preprint.repository)
        except:
            raise CommandError('Setting for repo with preprint not found preprint_id=' + preprint_id)

        p = PreprintToMerritt(preprint, reposetting) 
        p.process()
        return