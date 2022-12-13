import logging
import os
import time

from hikvision_client import HikvisionClient
from loggerinitializer import initialize_logger
from http_service import app


def main():
    logging.basicConfig(level=logging.DEBUG)
    cam = HikvisionClient('http://192.168.0.221', 'user', '1q2w3e4r')
    device_info = cam.get_status()
    logging.info(
        f"serial_number: {device_info.serial_number}, name: {device_info.device_name}, "
        f"firmware: {device_info.firmware_version}, firmware date {device_info.firmware_date_release}")
    # cam.background_download_pictures(os.path.abspath(os.curdir), only_with_number=False)
    # while True:
    #    cam.get_pictures()
    #    time.sleep(0.3)

    # cam.listener_events_server()
    cam.manual_cup(os.path.abspath(os.curdir), unrecognized_photo_save=True)
    logging.info("Starting loop manual cup")
    while True:
        # input("Press enter for manual_cup: \n")
        cam.manual_cup(os.path.abspath(os.curdir))


if __name__ == '__main__':
    initialize_logger("log")
    main()
