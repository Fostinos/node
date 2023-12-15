from LoRaMAC import LoRaMAC
from LoRaMAC import Region
from LoRaMAC import Device
from LoRaMAC import JoinStatus, TransmitStatus, ReceiveStatus

from .Keys import *

import time
import logging

class App():
    """
    Represents an application using the LoRaMAC protocol.

    Attributes:
        __logger (logging.Logger): The logger object for logging messages.
        __region (Region): The region of the LoRaWAN network.
        __device (Device): The device object representing the application's device.
        __LoRaWAN (LoRaMAC): The LoRaMAC object for handling LoRaWAN communication.
    """

    def __init__(self, region: Region, level: int = logging.DEBUG) -> None:
        """
        Initializes the App object.

        Args:
            region (Region): The region of the LoRaWAN network.
            level (int, optional): The logging level. Defaults to logging.DEBUG.
        """
        self.__logger = logging.getLogger("APP[MAIN]")
        self.__logger.setLevel(level)
        self.__logger.debug(f"App Initializing...")
        self.__region = region
        self.__device = Device(DEVEUI, APPEUI, APPKEY)
        self.__LoRaWAN = LoRaMAC(self.__device, self.__region)
        self.__LoRaWAN.set_logging_level(level)
        self.__LoRaWAN.set_callback(self.__on_join_callback, self.__on_transmit_callback, self.__on_receive_callback)
        self.__logger.debug(f"App Initialized")

    def run(self):
        """
        Runs The `App` continuously
        """
        self.__logger.debug(f"App Running")
        self.__LoRaWAN.join(max_tries=3, forced=True)
        while True:
            if self.__LoRaWAN.is_joined():
                self.__LoRaWAN.transmit(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x6, 0x07, 0x08, 0x09]), True)
            time.sleep(5)


########################## Callback functions

    def __on_join_callback(self, status: JoinStatus):
        """
        Callback function called when a join event occurs.

        Args:
            status (JoinStatus): The status of the join event.
        """
        self.__logger.info(f"{status}")
        if status == JoinStatus.JOIN_OK:
            self.__logger.debug(f"DEVICE : {self.__device.to_dict()}")
            print(self.__device.to_dict())
        if status == JoinStatus.JOIN_MAX_TRY_ERROR:
            self.__logger.debug(f"DEVICE : {self.__device.to_dict()}")

    def __on_transmit_callback(self, status: TransmitStatus):
        """
        Callback function called when a transmit event occurs.

        Args:
            status (TransmitStatus): The status of the transmit event.
        """
        self.__logger.info(f"{status}")

    def __on_receive_callback(self, status: ReceiveStatus, payload: bytes):
        """
        Callback function called when a receive event occurs.

        Args:
            status (ReceiveStatus): The status of the receive event.
            payload (bytes): The received payload.
        """
        self.__logger.info(f"{status}")
        if status == ReceiveStatus.RX_OK:
            self.__logger.debug(f"Receive Data = {list(payload)}")