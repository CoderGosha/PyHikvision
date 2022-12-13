import datetime
import logging
import os.path
import shutil
import time
import traceback
import urllib
import uuid
from threading import Thread
from time import sleep
from typing import List

import requests
import xmltodict
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib.parse import urljoin

from http_service import get_local_address, app
from model import DeviceInfo, CMSearchResult, PictureInformation, Fixation


class HikvisionClient:
    def __init__(self, host, login=None, password=None, timeout=3, isapi_prefix='ISAPI'):
        self.host = host
        self.login = login
        self.password = password
        self.timeout = float(timeout)
        self.isapi_prefix = isapi_prefix
        self.req = self._check_session()
        self.count_events = 1
        self.last_time = None
        self.known_play_uri = []

        self.download_path = None
        self.download_only_with_number = False
        self.download_fixation = List[Fixation]
        self.thread_download = Thread(target=self.__background_download__)

    def _check_session(self):
        """Check the connection with device
         :return request.session() object
        """
        full_url = urljoin(self.host, self.isapi_prefix + '/System/deviceInfo')
        session = requests.session()
        session.auth = HTTPBasicAuth(self.login, self.password)
        response = session.get(full_url)
        if response.status_code != 401:
            return session
        session.auth = HTTPDigestAuth(self.login, self.password)
        response = session.get(full_url)
        if response.status_code != 401:
            return session
        # response.raise_for_status()
        return session

    def get_status(self) -> DeviceInfo:
        full_url = urljoin(self.host, self.isapi_prefix + '/System/deviceInfo')
        response = self.req.get(url=full_url)
        return DeviceInfo.from_xml_str(response.text)

    def loop_events(self):
        data = """
        <SubscribeEvent version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
            <heartbeat>5</heartbeat>
            <eventMode>all</eventMode>
            <EventList>
            </EventList>
        </SubscribeEvent>
        """

        while True:
            try:
                full_url = urljoin(self.host, self.isapi_prefix + '/Event/notification/subscribeEvent')
                events = self.stream_request(method="post",
                                             full_url=full_url,
                                             data=data)
                logging.info(f"New events: {events}")
            except requests.ReadTimeout:
                pass

            except Exception as ex:
                logging.error(f"Method loop_events: {ex}, {traceback.format_exc()}")
                return
            finally:
                sleep(0.1)

    def stream_request(self, method, full_url, time_out=30, **data):
        events = []
        response = self.req.request(method, full_url, timeout=time_out, stream=True, **data)
        if response.status_code != 200:
            logging.warning(f"Method: {full_url}, returned code: {response.status_code} with text: {response.text}")
            return None

        for chunk in response.iter_lines(chunk_size=1024, delimiter=b'--boundary'):
            if chunk:
                xml = chunk.split(b'\r\n\r\n')[1].decode("utf-8")
                events.append(xml)
                if len(events) == self.count_events:
                    return events

    def set_callback(self, local_ip, port, url):
        logging.info(f"Set callback: {local_ip}:{port} with url: {url}")
        data = f"""
                <?xml version="1.0" encoding="UTF-8"?>
                <HttpHostNotification version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
                    <id>1</id>
                    <url>/{url}</url>
                    <protocolType>HTTP</protocolType>
                
                    <addressingFormatType>ipaddress</addressingFormatType>
                    <ipAddress>{local_ip}</ipAddress>
                    <hostName> </hostName>
                    <portNo>{port}</portNo>
                    <ANPR>
                        <detectionUpLoadPicturesType>all</detectionUpLoadPicturesType>
                    </ANPR>
                    <eventMode>all</eventMode>
                </HttpHostNotification>
                """

        full_url = urljoin(self.host, self.isapi_prefix + '/Event/notification/httpHosts/1')
        response = self.req.put(url=full_url, data=data)
        logging.info(f"Result callback: {response.status_code} with: {response.text}")

    def __get_pictures__(self, time_start, count=10) -> CMSearchResult:
        date_time_start = time_start.strftime("%Y-%m-%dT%H:%M:%SZ")
        date_time_end = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.last_time = datetime.datetime.now()
        request_id = uuid.uuid4()
        logging.debug(f"Trying get pictures: {request_id} start: {date_time_start} end: {date_time_end}")
        data = f"""
                <?xml version="1.0" encoding="utf-8"?>
                <CMSearchDescription><searchID>{request_id}</searchID>
                <trackIDList><trackID>120</trackID></trackIDList>
                <timeSpanList><timeSpan>
                <startTime>{date_time_start}</startTime>
                <endTime>{date_time_end}</endTime>
                <laneNumber></laneNumber><carType>all</carType><illegalType>all</illegalType></timeSpan>
                </timeSpanList><contentTypeList><contentType>metadata</contentType>
                </contentTypeList><maxResults>{count}</maxResults><searchResultPostion>0</searchResultPostion>
                <metadataList><metadataDescriptor>//recordType.meta.hikvision.com/timing</metadataDescriptor>
                <SearchProperity><plateSearchMask></plateSearchMask></SearchProperity></metadataList></CMSearchDescription>
                        """

        full_url = urljoin(self.host, self.isapi_prefix + '/ContentMgmt/search')
        response = self.req.post(url=full_url, data=data)
        logging.debug(f"Result: {response.status_code} with: {response.text}")

        return CMSearchResult.from_xml_str(response.text)

    def get_pictures(self):
        time_start = self.get_date_time_start()
        cms_result = self.__get_pictures__(time_start=time_start, count=20)
        logging.debug(f"Id: {cms_result.search_id}, count: {cms_result.count}")
        for result in cms_result.search_list:
            if result.play_back_uri not in self.known_play_uri:
                logging.debug(
                    f"Id: {result.track_id}, time: {result.time_start}, playback: {result.play_back_uri}, description: {result.description}")

                meta = self.__get_meta_data__(result.play_back_uri)
                logging.info(
                    f"New fixation number: {meta.number}, time: {result.time_start}, type: {meta.type}: color: {meta.color}")
                self.known_play_uri.append(result.play_back_uri)
                fixation = Fixation(url=result.play_back_uri, number=meta.number, date_time=result.time_start)
                # self.download_fixation.append(fixation)

    def listener_events_server(self):
        local_ip = get_local_address()
        port = 5010
        url = "test"
        self.set_callback(local_ip, port, url)
        #
        logging.info("Start http listener...")
        app.run(debug=True, port=port, host="0.0.0.0")

    def __get_meta_data__(self, play_back_uri) -> PictureInformation:
        request_id = uuid.uuid4()
        logging.debug(f"Trying get pictures: {request_id}")
        data = f"""
                <?xml version="1.0"?><downloadRequest version="1.0" xmlns="http://urn:selfextension:psiaext-ver10-xsd"><playbackURI>
                {play_back_uri}
                </playbackURI></downloadRequest>   """
        data = data.replace("&", "&amp;")
        full_url = urljoin(self.host, self.isapi_prefix + '/ITC/ContentMgmt/pictureInformation')
        response = self.req.post(url=full_url, data=data)
        logging.debug(f"Result: {response.status_code} with: {response.text}")

        return PictureInformation.from_xml_str(response.text)

    def get_date_time_start(self) -> datetime.datetime:
        if self.last_time is None:
            self.last_time = datetime.datetime.now() - datetime.timedelta(minutes=10)

        return self.last_time - datetime.timedelta(seconds=10)

    def background_download_pictures(self, path, only_with_number=False):
        download_path = os.path.join(path, "pictures")
        if not os.path.exists(download_path):
            os.mkdir(download_path)
        self.download_path = download_path
        self.download_only_with_number = only_with_number
        # self.thread_download.start()

    def __background_download__(self):
        logging.info(f"Download dir: {self.download_path}")
        while True:
            if len(self.download_fixation) > 0:
                fixation = self.download_fixation.pop(0)
                if fixation.number == "unknown" and self.download_only_with_number:
                    continue
                # Тут загрузка элемента
                logging.debug(f"Download: {fixation.date_time}, number: {fixation.number} with: {fixation.url}")
                name = f"{fixation.date_time.replcae('.', '_')}_{fixation.number}.jpg"
                self.__image_download__(self.download_path, fixation.url, name)
            time.sleep(0.1)

    def __image_download__(self, download_path, url, name):
        logging.debug(f"Download pictures: {url}")
        data = f"""
                       <?xml version="1.0"?><downloadRequest version="1.0" xmlns="http://urn:selfextension:psiaext-ver10-xsd"><playbackURI>
                       {url}
                       </playbackURI></downloadRequest>   """
        data = data.replace("&", "&amp;")
        full_url = urljoin(self.host, self.isapi_prefix + '/ITC/ContentMgmt/download')
        response = self.req.get(url=full_url, data=data, stream=True)

        if response.status_code == 200:
            with open(os.path.join(download_path, name), 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

        logging.debug(f"Download finish: {os.path.join(download_path, name)}")

    def manual_cup(self, path, unrecognized_photo_save=False):
        logging.debug(f"Trying manual cup")
        time_start = datetime.datetime.utcnow()
        full_url = urljoin(self.host, self.isapi_prefix + '/ITC/manualCap')
        response = self.req.put(url=full_url)
        # logging.debug(f"Result: {response.status_code} with: {response.text}")
        date = datetime.datetime.now().strftime("%Y_%d_%m_%H_%M_%S")
        filename = date + ".jpg"
        path = os.path.join(path, "manual_pictures")
        if not os.path.exists(path):
            os.mkdir(path)

        if response.status_code == 200:
            response.raw.decode_content = True
            number = self.parse_message_from_byte(response.content, unrecognized_photo_save=unrecognized_photo_save)
            logging.debug(f"Manual Cup, time {datetime.datetime.utcnow() - time_start}: Response: {number}")

    def __save_image__(self, download_path, name, raw):
        with open(os.path.join(download_path, name), 'wb') as f:
            shutil.copyfileobj(raw, f)

    def parse_message_from_byte(self, content, unrecognized_photo_save=False):
        """
         1 - Пробуем разобрать xml в посылке на 272 байт
         2- При ошибке ищем слово unknown
         3 - Альтернативные посылки пока сохраняем
        :param content:
        :param unrecognized_photo_save:
        :return:
        """
        if len(content) == 272:
            try:
                response = content[0:272].decode().lstrip('\x00').rstrip('\x00')
                xml_dict = xmltodict.parse(response)
                if 'ResponseStatus' in xml_dict and "statusString" in xml_dict["ResponseStatus"] and \
                        xml_dict["ResponseStatus"]['statusString'] == "OK":
                    return "Ok"
                else:
                    logging.info(f'Error parse: {response}')
            except UnicodeDecodeError:
                logging.debug("Parse error")

        if len(content) > 300:
            try:
                recognize = False
                response = content[88:100].decode().lstrip('\x00').rstrip('\x00')
                if response == "unknown":
                    recognize = False
                else:
                    recognize = True
                    logging.info(f'!!! Detected number: {response}')
                    # logging.debug(content)
                return response
            except UnicodeDecodeError:
                logging.info("Parse error")
                logging.debug(content)
        return None
