"""eTranslation wrapper"""

import base64
import json
import os
import time

import paramiko
import requests

class Client(object):
    """eTranslation client mimicking Google Translate"""
    def __init__(self, credentials_path="./credentials.json"):
        with open(credentials_path, "r") as json_file:
            credentials = json.load(json_file)
            etranslation_user = credentials["etranslation"]["username"]
            etranslation_pwd = credentials["etranslation"]["password"]
            sftp_username = credentials["sftp"]["username"]
            sftp_password = credentials["sftp"]["password"]
            sftp_server = credentials["sftp"]["server"]

        transport = paramiko.Transport((sftp_server, 22))
        transport.connect(username=sftp_username, password=sftp_password)
        self.sftp = paramiko.SFTPClient.from_transport(transport)
        self.sftp_string = f"sftp://{sftp_username}:{sftp_password}@{sftp_server}:22/www/translations"

        self.session = requests.Session()
        self.url = "https://webgate.ec.europa.eu/etranslation/si/translate"

        self.credentials = requests.auth.HTTPDigestAuth(etranslation_user, etranslation_pwd)
        self.headers = {"Content-Type": "application/json"}

    def translate(self, text, source_language=None, format_=None):
        """Translate with eTranslation REST API"""
        text = text.encode('utf-8')
        encoded = base64.b64encode(text).decode()
        body = '''{
            "priority" : 0,
            "externalReference" : "123",
            "callerInformation" : {
                "application" : "DORIS_CNECT20151014",
                "username" : "DorisMTService"
            },
            "documentToTranslateBase64" : {
                "content" : "''' + encoded + '''",
                "format" : "''' + format_ + '''"
            },
            "sourceLanguage" : "''' + source_language.upper() + '''",
            "targetLanguages" : ["EN"],
            "domain" : "GEN",
            "requesterCallback" : "https://linkedopendata.eu",
            "errorCallback" : "https://linkedopendata.eu",
            "destinations" : {
                "sftpDestinations" : ["''' + self.sftp_string + '''"]
            }
        }'''

        resp = self.session.post(self.url, headers=self.headers, data=body, auth=self.credentials)
        if resp.status_code != 200:
            return resp.status_code

        request_id = resp.content.decode()
        filename = f"{request_id}_EN.txt"
        remote_filename = f'www/translations/{filename}'
        local_filename = f'/home/max/{filename}'
        translated = False
        while not translated:
            try:
                self.sftp.get(remote_filename, local_filename)
                translated = True
            except FileNotFoundError:
                time.sleep(1)
        with open(local_filename) as f:
            translation = f.read().strip()
        os.remove(local_filename)
        return translation
