"""
This module contains the logic for the Merritt plugin for Janeway
"""

__copyright__ = "Copyright (c) 2023, The Regents of the University of California"
__author__ = "Mahjabeen Yucekul"
__license__ = "BSD 3-Clause"
__maintainer__ = "California Digital Library"


import os
import re
import shutil
import requests
from utils.logger import get_logger
from django.utils import timezone

from .models import PreprintMerrittRequests, MerrittQueue
from django.conf import settings as django_settings
from pathlib import Path
from zipfile import ZipFile

logger = get_logger(__name__)

# create a class that takes preprint id and does all the working needed to 
# build zip file for it
"""
Process one preprint by sending it to Merritt using repo setting information 
about Merritt collection for the preprint
"""
class PreprintToMerritt:
    preprint = None
    reposetting = None

    def __init__(self, preprint, reposetting):
        self.preprint = preprint
        self.reposetting = reposetting

    def process(self):
         # create a PreprintMerrittRequests to keep all the information related to curl request to Merritt
        request = PreprintMerrittRequests(preprint = self.preprint, request_date=timezone.now())
        request.save()
        # update entry in MerrittQueue for the preprint
        qitem = MerrittQueue.objects.get_or_create(preprint = self.preprint, defaults={'queue_date':timezone.now() })[0]
        qitem.status = MerrittQueue.ItemStatus.PROCESSING
        qitem.save()
        try:
            # put together the article and metadata to create a zip for Merritt
            z = ZipForPreprint(self.preprint, self.preprint.repository)
            zipfile = z.createZip()
        except Exception as e:
            # save error message in db
            request.response = str(e)
            request.status = PreprintMerrittRequests.SubmissionStatus.PREP_ERROR
            request.save()
            raise
        try:
            # send the zip file to Merritt using curl command
            m = MerrittForPreprint(self.preprint, self.reposetting.merritt_collection, zipfile, request)
            m.sendRequest()
            request.status = PreprintMerrittRequests.SubmissionStatus.SENT
            request.save()
        except Exception as e:
            # save error message in db
            request.response = str(e)
            request.status = PreprintMerrittRequests.SubmissionStatus.SEND_ERROR
            request.save()
            raise
        
        # clear temp
        ZipForPreprint.clearTmp()
        print("DONE")

"""
Create a zip file for upload to Merritt by combining metadata from OAI endpoint and article file
"""
class ZipForPreprint:
    preprint = None
    repo = None
    tmpfolder = None
    filepath_base = "/apps/eschol/janeway/src/files/"
    def __init__(self, ppobj, repoobj):
        print("creating zip for preprint")
        self.preprint = ppobj
        self.repo = repoobj

    def createZip(self):
        print("creating zip file")
        # create temp folder if needed
        self.tmpfolder = django_settings.MERRITT_TMP + str(self.preprint.id)
        zipfile = f'{django_settings.MERRITT_TMP}{self.preprint.id}.zip'
        if not os.path.exists(django_settings.MERRITT_TMP):
            os.mkdir(django_settings.MERRITT_TMP)

        # empty the folder if needed
        if os.path.exists(self.tmpfolder):
            shutil.rmtree(self.tmpfolder)
        os.mkdir(self.tmpfolder)

        # copy files temp folder
        articlepath = self.copyArticle()
        metadatapath = self.generateMetadata()

        # generate zip file  
        with ZipFile(zipfile, 'w') as zip_object:
            zip_object.write(articlepath)
            zip_object.write(metadatapath)
        assert(os.path.exists(zipfile))
        return zipfile

    def copyArticle(self):
        print("copy article file")
        fullpath = self.filepath_base + str(self.preprint.submission_file.file)
        temppath = self.tmpfolder + '/' + Path(fullpath).name
        shutil.copy(fullpath, temppath)
        return temppath

    def generateMetadata(self):
        print("generate meta data")
        params = {
            'verb': 'GetRecord',
            'identifier': f'oai:{self.repo.short_name}:id:{self.preprint.id}',
            'metadataPrefix': 'jats'
        }
        response = requests.get(f'https://{self.repo.domain}/api/oai', params=params)
        # save the metadata in temp folder
        xmlname = f'{self.tmpfolder}/meta_{self.preprint.id}.xml'
        with open(xmlname, "a") as f:
            f.write(response.text)
        return xmlname

    def clearTmp():
        shutil.rmtree(django_settings.MERRITT_TMP)
    

"""
Send zip to Merritt
"""
class MerrittForPreprint:
    preprint = None
    collection = None
    zipname = None
    request = None
    def __init__(self, ppobj, colname, zipname, request):
        print("created Merritt for preprint")
        # give me the repo object from the plugin table with the repo merritt info
        self.preprint = ppobj
        self.collection = colname
        self.zipname = zipname
        self.request = request


    def sendRequest(self):
        print("create request and send Merritt update")
        files = {
            'file': open(self.zipname, 'rb'),
            'type': (None, 'container'),
            'submitter': (None, django_settings.MERRITT_USER),
            'title': (None, re.sub(r'[^a-zA-Z0-9 ]', '', self.preprint.title)), 
            'date':(None, str(self.preprint.date_published)),
            'creator': (None, self.getCreators()),
            'responseForm': (None, 'xml'),
            'profile': (None, self.collection),
            'localIdentifier': (None, self.preprint.id),
        }
        # save the request info
        self.request.request_detail = str(files)
        self.request.save()
        # send request
        response = requests.post(django_settings.MERRITT_URL, files=files, auth=(django_settings.MERRITT_USER, django_settings.MERRITT_KEY))
        # save response
        self.request.response = response.text
        self.request.save()
        return

    def extractIDs(self, output):
        print("extracting ids")
        lines = output.splitlines()
        for line in lines:
            if "<bat:batchID>" in line:
                batchId = line.split('>')[1].split('<')[0]
            if "<bat:jobID>" in line:
                jobId = line.split('>')[1].split('<')[0]
        print(batchId)
        print(jobId)

    def getCreators(self):
        print("get the creators")        
        names = []
        count = 0
        authors = self.preprint.preprintauthor_set.all()
        # add first six authors - same as eschol citation format
        for author in authors:
            if count == 6:
                break
            contributor = author.account
            if contributor.last_name:
                count += 1
                name = contributor.last_name
                if contributor.first_name:
                    name += f', {contributor.first_name[0]}.'
                names.append(name)

        creators = "; ".join(names)
        if len(authors) > 6:
            creators += ", et al."
        return creators
