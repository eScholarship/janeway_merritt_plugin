"""
This module contains the logic for the Merritt plugin for Janeway
"""

__copyright__ = "Copyright (c) 2023, The Regents of the University of California"
__author__ = "Mahjabeen Yucekul"
__license__ = "BSD 3-Clause"
__maintainer__ = "California Digital Library"


import os
import re
import subprocess

from utils.logger import get_logger
from django.utils import timezone

from .models import PreprintMerrittRequests, MerrittQueue
from django.conf import settings as django_settings
from pathlib import Path

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
        print("DONE")

"""
Create a zip file for upload to Merritt by combining metadata from OAI endpoint and article file
"""
class ZipForPreprint:
    preprint = None
    repo = None
    tmpfolder = None
    metadata_urlbase = '"https://{param1}/api/oai/?verb=GetRecord&identifier=oai:{param2}:id:{param3}&metadataprefix=oai_dc"'
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
        print(self.tmpfolder)
        # create folder if needed
        os.system(f'mkdir -p {self.tmpfolder}')
        # empty the folder if needed
        os.system(f'rm {self.tmpfolder}/*')

        # copy files temp folder
        self.copyArticle()
        self.generateMetadata()

        # generate zip file  
        zipcommand = f'zip -r {zipfile} {self.tmpfolder}/'
        print(zipcommand)
        result = os.system(zipcommand)
        assert(result == 0)
        return zipfile

    def copyArticle(self):
        print("copy article file")
        print(self.preprint.title)
        print(self.preprint.submission_file.file)
        fullpath = self.filepath_base + str(self.preprint.submission_file.file)
        temppath = self.tmpfolder + '/' + Path(fullpath).name
        print("copy from " + fullpath)
        print("copy to " + temppath)
        result = os.system("cp {} {}".format(fullpath, temppath))
        assert(result == 0)

    def generateMetadata(self):
        print("generate meta data")
        print(self.repo.short_name)

        # get url from repo
        metadata_url = self.metadata_urlbase.format(param1=self.repo.domain, param2= self.repo.short_name, param3=self.preprint.id)
        print(metadata_url)

        # save the metadata in temp folder
        xmlname = f'{self.tmpfolder}/meta_{self.preprint.id}.xml'
        result = os.system("curl {} > {}".format(metadata_url, xmlname))
        assert(result == 0)
    

"""
Send zip to Merritt
"""
class MerrittForPreprint:
    # get merritt user name, password and url from settings
    merritt_base = 'curl -u {param1} -F "file=@{param2}" -F "type=container" -F "submitter={param3}" "title={param4}" --form-string "creator={param5}" -F "responseForm=xml" -F "profile={param6}" -F "localIdentifier={param7}" "{param8}"'
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
        print("create curl request and send update")

        # the zip file is in tmp folder
        merritt_command = self.merritt_base.format(
            param1 = f'{django_settings.MERRITT_USER}:{django_settings.MERRITT_KEY}',
            param2 = self.zipname,
            param3 = django_settings.MERRITT_USER,
            param4 = re.sub(r'[^a-zA-Z0-9 ]', '', self.preprint.title), 
            param5 = self.getCreators(),
            param6 = self.collection,
            param7 = self.preprint.id,
            param8 = django_settings.MERRITT_URL
            )

        # save this request
        print(merritt_command)
        self.request.request_detail = merritt_command
        self.request.save()
        output = subprocess.getoutput(merritt_command)
        print("This is the output")
        print(output)
        self.request.response = output
        self.request.save()
        return output

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
