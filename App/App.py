from LoRaMAC import LoRaMAC
from LoRaMAC import Region
from LoRaMAC import Device
from LoRaMAC import JoinStatus, TransmitStatus, ReceiveStatus

import os
import json
import time
import logging

from .Sensors import Relay, Banana

class App():
    """
    Represents an application using the LoRaMAC protocol.

    Attributes:
        __logger (logging.Logger): The logger object for logging messages.
        __region (Region): The region of the LoRaWAN network.
        __device (Device): The device object representing the application's device.
        __LoRaWAN (LoRaMAC): The LoRaMAC object for handling LoRaWAN communication.
    """
    
    VOLTAGE_RESOLUTION = 1000

    APP_CHANNEL        = 0xFF
    TYPE_TIMESTAMP     = 0x00
    TYPE_RELAY         = 0x01
    TYPE_BANANA        = 0x02

    def __init__(self, region: Region, level: int = logging.DEBUG) -> None:
        """
        Initializes the App object.

        Args:
            region (Region): The region of the LoRaWAN network.
            level (int, optional): The logging level. Defaults to logging.DEBUG.
        """
        self.__logger = logging.getLogger("APP[MAIN]")
        self.__logger.setLevel(level)
        self.__logger.info(f"App Initializing...")
        self.__region = region
        self.__config = dict()
        self.__load_config()
        self.__device = Device(self.__config["DevEUI"], self.__config["AppEUI"], self.__config["AppKey"])
        self.__LoRaWAN = LoRaMAC(self.__device, self.__region)
        self.__LoRaWAN.set_logging_level(level)
        self.__LoRaWAN.set_callback(self.__on_join_callback, self.__on_transmit_callback, self.__on_receive_callback)
        self.__relay = Relay()
        self.__banana = Banana()
        self.__logger.info(f"App Initialized")

    def run(self):
        """
        Runs The `App` continuously
        """
        self.__logger.info(f"App Running")
        self.__LoRaWAN.join(max_tries=3, forced=True)
        while True:
            if self.__LoRaWAN.is_joined():
                self.__logger.info("The device transmits data")
                data = bytearray([App.APP_CHANNEL, App.TYPE_TIMESTAMP])
                data = data + int(time.time()).to_bytes(4)
                data = data + bytearray([App.APP_CHANNEL, App.TYPE_RELAY])
                data = data + int(self.__relay.read_voltage(0) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__relay.read_voltage(1) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__relay.read_voltage(2) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__relay.read_voltage(3) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + bytearray([App.APP_CHANNEL, App.TYPE_BANANA])
                data = data + int(self.__banana.read_voltage(0) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__banana.read_voltage(1) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__banana.read_voltage(2) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                data = data + int(self.__banana.read_voltage(3) * App.VOLTAGE_RESOLUTION).to_bytes(4)
                self.__LoRaWAN.transmit(bytes(data), True)
                time.sleep(299)
            time.sleep(1)

########################## Config Storage functions
            
    def __load_config(self)->bool:
        try:
            currentdir = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(currentdir, "config.json")) as file:
                self.__config = dict(json.load(file))
            self.__config.get("DevEUI")
            self.__config.get("AppEUI")
            self.__config.get("AppKey")
            self.__config.get("config")
            return True
        except:
            self.__logger.critical(f"Load config file: critical error")
            raise ValueError("Verify config.json file in the App folder")

    def __save_config(self)->bool:
        try:
            currentdir = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(currentdir, "config.json"), "w") as file:
                file.write(json.dumps(self.__config, indent=4))
            return True
        except:
            self.__logger.warning(f"Save configuration file")
            return False


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