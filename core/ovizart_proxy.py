__author__ = 'ggercek'

import json
import requests
import os
import ovizutil


class OvizartProxy():

    LOGIN_URL = 'login'
    UPLOAD_URL = 'upload'
    START_URL = 'start'
    LIST_ANALYSIS = 'analysis'
    ANALYZER_URL = 'analyzer'
    GET_PCAP_URL = 'pcap'
    GET_REASSEMBLED_URL = 'reassembled'
    GET_ATTACHMENT_URL = 'attachment'

    def __init__(self, protocol='https', host='localhost', port=9009):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.login_success = False
        self.cookies = None
        self.userid = None
        self.username = None
        self.password = None

    def __generateLink(self, url):
        return "%s://%s:%s/%s"%(self.protocol, self.host, self.port, url)

    def login(self, username, password):
        url = self.__generateLink(OvizartProxy.LOGIN_URL)
        response = requests.post(url, verify=False, headers={'content-type': 'application/json'},
                                 data=json.dumps({'username': username, 'password': password}))

        # Check for login success?
        result = json.loads(response.content)
        if result['Status'] == 'OK':
            userid = result['userid']
            self.login_success = True
            self.cookies = response.cookies
            self.username = username
            self.password = password
            self.userid = userid

        return result

    def uploadFile(self, filename, fileobj=None):
        result = "NA"
        filepath = os.path.abspath(filename)
        filename = os.path.basename(filepath)

        if fileobj:
                url = self.__generateLink(OvizartProxy.UPLOAD_URL) + '/' + filename
                response = requests.post(url, verify=False, data=fileobj, headers={'content-type': 'application/octet-stream'},
                                         cookies=self.cookies)
                result = json.loads(response.content)

        elif filename:
            url = self.__generateLink(OvizartProxy.UPLOAD_URL) + '/' + filename
            with open(filepath, 'r') as f:
                # Form based approach
                #response = requests.post(url, verify=False, files={'file': (filename, f)}, cookies=self.cookies)
                # Stream based approach
                response = requests.post(url, verify=False, data=f, headers={'content-type': 'application/octet-stream'},
                                         cookies=self.cookies)
                result = json.loads(response.content)

        return result

    def start(self):
        url = self.__generateLink(OvizartProxy.START_URL)
        response = requests.post(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.cookies)
        result = json.loads(response.content)
        return result

    def getAnalysis(self, analysisId=None):
        url = self.__generateLink(OvizartProxy.LIST_ANALYSIS)

        if analysisId:
            url = url + '/' + analysisId

        response = requests.get(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.cookies)
        if response.content:
            #print 'response.content:', response.content
            result = json.loads(response.content)
        else:
            result = {}
        return result

    def removeAnalysisById(self, analysisId):
        url = self.__generateLink(OvizartProxy.LIST_ANALYSIS)
        if analysisId:
            url = url + '/' + analysisId

        response = requests.delete(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.cookies)
        if response.content:
            #print 'response.content:', response.content
            result = json.loads(response.content)
        else:
            result = {}
        return result

    def addAnalyzer(self, filename):
        result = None
        filepath = os.path.abspath(filename)
        filename = os.path.basename(filepath)

        if filename:
            url = self.__generateLink(OvizartProxy.ANALYZER_URL) + '/' + filename
            with open(filepath, 'r') as f:
                response = requests.put(url, verify=False, data=f, headers={'content-type': 'application/octet-stream'},
                                         cookies=self.cookies)
                result = json.loads(response.content)

        return result

    def getPcap(self, analysisId, streamKey):
        url = self.__generateLink(OvizartProxy.GET_PCAP_URL) + '/' + analysisId + '/' + streamKey
        return self.__downloadFile(url)

    def getReassembled(self, analysisId, streamKey, trafficType):
        url = self.__generateLink(OvizartProxy.GET_REASSEMBLED_URL) + '/' + analysisId + '/' + streamKey + '/' + trafficType
        return self.__downloadFile(url)

    def getAttachment(self, analysisId, streamKey, filePath):
        url = self.__generateLink(OvizartProxy.GET_ATTACHMENT_URL) + '/' + analysisId + '/' + streamKey + '/' + filePath
        return self.__downloadFile(url)

    def __downloadFile(self, url):
        r = requests.get(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.cookies, stream=True)  # here we need to set stream = True parameter
        tempFolder = '/tmp/%s'%ovizutil.getTimestampStr()
        os.mkdir(tempFolder)
        basename = r.headers['content-disposition'].split('filename=')[-1]
        # TODO: Add error handling !!!
        local_filename = '%s/%s' % (tempFolder, basename)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return local_filename