from .loramac_database import Database
from .loramac_wrapper import WrapperLoRaMAC
from .loramac_types import MessageType
from .loramac_region import Region
from .loramac_device import Device
from .loramac_status import JoinStatus, TransmitStatus, ReceiveStatus, RadioStatus
from .loramac_command import MacCommand
from .loramac_settings import *
from .LoRaRF import SX126x

from threading import Thread, Semaphore
import logging
import random
import time

logging.basicConfig(format='%(asctime)s.%(msecs)03d   %(levelname)-8s %(name)s: %(message)s',
                level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

logging.getLogger("DRIVER[SX126x]").setLevel(logging.INFO)
class LoRaMAC():
    """
    The `LoRaMAC` class is a Python implementation of a LoRaWAN MAC layer. 
    It provides methods for joining a LoRaWAN network, transmitting data, and receiving data.
    The class uses a LoRaRF library for low-level communication with the LoRa radio module.

    Note:
        Only LoRaWAN Class C device is implemented (can work with LoRaWAN Class A)

    Example Usage:
        device  = Device(DevEUI, AppEUI, AppKey)\n
        region  = Region.US915\n
        LoRaWAN = LoRaMAC(device, region)\n
        LoRaWAN.set_callback(on_join_callback, on_transmit_callback, on_receive_callback)\n
        LoRaWAN.join()\n
        LoRaWAN.transmit(payload, confirmed=True)\n

    Main functionalities:
    - Joining a LoRaWAN network
    - Transmitting data
    - Receiving data

    Methods:
    - is_joined(self) -> bool: Returns whether the device has successfully joined the network.
    - set_callback(self, on_join, on_transmit, on_receive): Sets the callback functions for join, transmit, and receive events.
    - join(self, max_tries:int=1, forced:bool=False) -> bool: Joins the LoRaWAN network.
    - transmit(self, payload:bytes, confirmed:bool=False) -> bool: Transmits data over the LoRaWAN network.
    - set_logging_level(self, level=logging.INFO): Sets the logging level for the `LoRaMAC` object.

    Fields:
    - _device: The device object associated with the `LoRaMAC` object.
    - _region: The region object associated with the `LoRaMAC` object.
    - _on_join: Callback function for join event.
    - _on_transmit: Callback function for transmit event.
    - _on_receive: Callback function for receive event.
    - _logger: Logger object for logging messages.
    - _channel: Current channel for communication.
    - _spreading_factor: Current spreading factor for communication.
    - _LoRa: LoRaRF object for low-level communication with the LoRa radio module.
    - _db: Database object for storing device information.
    - _LoRaSemaphore: Semaphore object for thread synchronization.
    - _thread: Thread object for running the background task.
    """
    
    def __init__(self, device:Device, region:Region):
        """
        Initializes the LoRaMAC object with the provided device and region.
    
        Args:
            device (Device): The device object associated with the LoRaMAC object.
            region (Region): The region object associated with the LoRaMAC object.
        """
        self._device = device
        self._region = region
        self._on_join = None
        self._on_transmit = None
        self._on_receive = None
        self._logger = logging.getLogger("APP[LoRaMAC]")
        self._logger.setLevel(logging.DEBUG)
        self._logger.debug(f"LoRaMAC Initializing...")
        self._channel = self._region.value.UPLINK_CHANNEL_MIN
        self._spreading_factor = self._region.value.SPREADING_FACTOR_MAX
        self._LoRa = SX126x()
        self._Mac = MacCommand()
        self._LoRaIrqStatus = self._LoRa.STATUS_DEFAULT
        db = Database()
        db.open()
        # Create table if not exists
        db.create_table()
        # Get device info if exists
        device_dict = db.get_device(device.DevEUI.hex())
        if device_dict is None:
            # Insert device info if not exists
            db.insert_device(device.DevEUI.hex(), device.AppEUI.hex(), device.AppKey.hex())
        else:
            # Restore device if exists
            self._device.set_device(device_dict)
        db.close()
        self._LoRaSemaphore = Semaphore()
        self._LoRaSemaphore.release()
        self._thread = Thread(target=self.__background_task, name="LoRaMAC Service", daemon=True)
        self._logger.debug(f"LoRa Radio Initializing...")
        self._LoRa.begin(RADIO_SPI_BUS_ID, RADIO_SPI_CS_ID, RADIO_RESET_PIN, RADIO_BUSY_PIN,
                         RADIO_IRQ_PIN, RADIO_TX_ENABLE_PIN, RADIO_RX_ENABLE_PIN)
        self._logger.debug(f"LoRa Radio Initialized")
        self._thread.start()
        self._logger.debug(f"LoRaMAC Initialized")

    def is_joined(self)->bool:
        """
        Returns a boolean value indicating whether the device has successfully joined the LoRaWAN network.
    
        Returns:
            True if the device has joined the LoRaWAN network, False otherwise.
        """
        return self._device.isJoined

    def set_callback(self, on_join, on_transmit, on_receive):
        """
        Set the callback functions for the on_join, on_transmit, and on_receive events in the `LoRaMAC` object.

        Args:
            on_join (function): A function that will be called when the device successfully joins the network.
            on_transmit (function): A function that will be called when the device transmits data.
            on_receive (function): A function that will be called when the device receives data.

        Returns:
            None

        Example Usage:
            def on_join_callback(status:JoinStatus):\n
                print(status)\n

            def on_transmit_callback(status:TransmitStatus):
                print(status)\n

            def on_receive_callback(status:ReceiveStatus, payload:bytes):\n
                print(status)\n
                if status == ReceiveStatus.RX_OK:\n
                    print("Data received = ", payload)\n
            
            device  = Device(DevEUI, AppEUI, AppKey)\n
            region  = Region.US915\n
            LoRaWAN = LoRaMAC(device, region)\n
            LoRaWAN.set_callback(on_join_callback, on_transmit_callback, on_receive_callback)\n
        """
        self._logger.debug(f"Events callback functions setting...")
        self._on_join = on_join
        self._on_transmit = on_transmit
        self._on_receive = on_receive

    def join(self, max_tries:int=1, forced:bool=False)->bool:
        """
        Join the network.

        Args:
            max_tries (int): The maximum number of join attempts. Default is 1.
            forced (bool): Whether to force the join process. Default is False.

        Returns:
            bool: True if the join process started, False otherwise.

        Example Usage:
            device  = Device(DevEUI, AppEUI, AppKey)\n
            region  = Region.US915\n
            LoRaWAN = LoRaMAC(device, region)\n
            joining = LoRaWAN.join(max_tries=3, forced=True)\n

        """
        if max_tries > 0:
            self._device.join_max_tries = max_tries - 1
        else:
            self._logger.debug(f"Join max try error")
            if callable(self._on_join):
                self._on_join(JoinStatus.JOIN_MAX_TRY_ERROR)
            return False
        
        if not forced and self._device.isJoined:
            self._logger.debug(f"Already Joined")
            if callable(self._on_join):
                self._on_join(JoinStatus.JOIN_OK)
            return True
        
        self._device.isJoined = False
        if not self.__lorawan_join_request():
            if callable(self._on_join):
                self._on_join(JoinStatus.JOIN_REQUEST_ERROR)
            return False
        
        if self._region == Region.EU868:
            self._channel = random.randint(self._region.value.UPLINK_CHANNEL_MIN, Region.EU868.value.JOIN_CHANNEL_MAX)
        else:
            self._channel = self.__random_channel()
        self._spreading_factor = self._region.value.SPREADING_FACTOR_MAX
        
        self._logger.info(f"Joining...")
        self._LoRaSemaphore.acquire()
        self.__radio_tx_mode()
        tx_time = time.time()
        if self.__radio_transmit(delay=JOIN_RX1_DELAY):
            # Transmit ok
            self.__radio_rx1_mode()
            self._device.rx2_window_time = tx_time + JOIN_RX2_DELAY
            self._LoRaSemaphore.release()
            return True
        else:
            # Transmit error
            self.__radio_rx2_mode()
            self._LoRaSemaphore.release()
            if self._device.join_max_tries > 0:
                    self.join(self._device.join_max_tries)
            elif callable(self._on_join):
                self._on_join(JoinStatus.JOIN_MAX_TRY_ERROR)
                return True
            

    def transmit(self, payload:bytes, confirmed:bool=False)->bool:
        """
        Transmits data over the LoRaWAN network.

        Args:
            payload (bytes): The data to be transmitted as a byte array.
            confirmed (bool, optional): Whether the transmission should be confirmed by the network. Default is False.

        Returns:
            bool: True if the transmission process started, False otherwise.
        """
        self._device.uplinkMacPayload = payload
        if not self._device.isJoined:
            self._logger.debug(f"Uplink : join error")
            if callable(self._on_transmit):
                self._on_transmit(TransmitStatus.TX_JOIN_ERROR)
            return False
        
        if not self.__lorawan_data_up(confirmed):
            if callable(self._on_transmit):
                self._on_transmit(TransmitStatus.TX_PAYLOAD_ERROR)
            return False
        
        self._channel = self.__random_channel()
        self._spreading_factor = self.__random_spreading_factor()
        
        self._logger.info(f"Transmitting...")
        self._LoRaSemaphore.acquire()
        self.__radio_tx_mode()
        if self.__radio_transmit(delay=UPLINK_RX1_DELAY):
            # Transmit ok
            rx1_time = time.time()
            self.__radio_rx1_mode()
            self._device.rx2_window_time = rx1_time + 1
            self._LoRaSemaphore.release()
            self._Mac.answer = None
            return True
        else:
            # Transmit error
            self.__radio_rx2_mode()
            self._LoRaSemaphore.release()
            return False
    
    def stack_transmit(self)->bool:
        self._LoRaSemaphore.acquire()
        self._device.uplinkMacPayload = bytes([])
        if not self.__lorawan_data_up(False, 0):
            self._LoRaSemaphore.release()
            return False
        if self._region == Region.EU868:
            self._channel = random.randint(self._region.value.UPLINK_CHANNEL_MIN, Region.EU868.value.JOIN_CHANNEL_MAX)
        else:
            self._channel = self.__random_channel()
        self._spreading_factor = self._region.value.SPREADING_FACTOR_MAX
        self._logger.info(f"Stack transmits empty payload on fPort 0")
        self.__radio_tx_mode()
        if self.__radio_transmit(delay=UPLINK_RX1_DELAY):
            # Transmit ok
            rx1_time = time.time()
            self.__radio_rx1_mode()
            self._device.rx2_window_time = rx1_time + 1
            self._LoRaSemaphore.release()
            self._Mac.answer = None
            return True
        else:
            # Transmit error
            self.__radio_rx2_mode()
            self._LoRaSemaphore.release()
            return False
    
    def set_logging_level(self, level:int=logging.INFO):
        """
        Sets the logging level for the `LoRaMAC`.

        Args:
            level (int): The logging level to be set. Default is logging.INFO.

        Returns:
            None
        """
        self._logger.setLevel(level)


    def __background_task(self):
        while True:
            
            if not self._LoRaSemaphore.acquire(timeout=0.5):
                time.sleep(0.5)
                continue

            if self._device.rx2_window_time > 0 and time.time() >= self._device.rx2_window_time:
                self._device.rx2_window_time = -1
                if self._device.isJoined and self._device.confirmed_uplink:
                    self._device.rx2_window_timeout = time.time() + UPLINK_RX2_DELAY
                if not self._device.isJoined:
                    self._device.rx2_window_timeout = time.time() + JOIN_RX2_DELAY
                self.__radio_rx2_mode()
                self._LoRaSemaphore.release()
                continue
            
            if self._device.rx2_window_timeout > 0 and time.time() >= self._device.rx2_window_timeout:
                self._device.rx2_window_timeout = -1
                if self._device.isJoined and self._device.confirmed_uplink and not self._device.AckDown:
                    if callable(self._on_receive):
                        self._on_receive(ReceiveStatus.RX_TIMEOUT_ERROR, bytes([]))
                if not self._device.isJoined: 
                    if self._device.join_max_tries > 0:
                        self.join(self._device.join_max_tries)
                    elif callable(self._on_join):
                        self._on_join(JoinStatus.JOIN_MAX_TRY_ERROR)

            time.sleep(0.2)
            self._LoRa.wait(1)
            if self._LoRa.available() == 0:
                self._LoRaSemaphore.release()
                continue

            time.sleep(0.2)
            self._device.downlinkPhyPayload = self.__radio_receive(delay=1)
            if len(self._device.downlinkPhyPayload) == 0:
                self._LoRaSemaphore.release()
                continue
            if len(self._device.downlinkPhyPayload) < 10:
                self._logger.error(f"Downlink PhyPayload")
                self.__radio_rx2_mode()
                self._LoRaSemaphore.release()
                continue
            
            if self._device.rx2_window_time > -100:
                self.__radio_rx2_mode()
            
            self._LoRaSemaphore.release()
            self.__lorawan_message_type()
            if self._device.message_type == MessageType.JOIN_ACCEPT:
                if self._device.isJoined:
                    continue
                self._device.rx2_window_time = -1
                self._device.rx2_window_timeout = -1
                if not self.__lorawan_join_accept():
                    if self._device.join_max_tries > 0:
                            self.join(self._device.join_max_tries)
                    elif callable(self._on_join):
                        self._on_join(JoinStatus.JOIN_ACCEPT_ERROR)
                elif callable(self._on_join):
                        self._on_join(JoinStatus.JOIN_OK)
            
            elif self._device.message_type == MessageType.CONFIRMED_DATA_DOWN or \
                self._device.message_type  == MessageType.UNCONFIRMED_DATA_DOWN:
                if not self._device.isJoined:
                    continue
                self._device.rx2_window_time = -1
                self._device.rx2_window_timeout = -1
                if self._device.message_type == MessageType.CONFIRMED_DATA_DOWN:
                    self._device.Ack = True
                else:
                    self._device.Ack = False

                if not self.__lorawan_data_down():
                    if callable(self._on_receive):
                        self._on_receive(ReceiveStatus.RX_PAYLOAD_ERROR, bytes([]))
                else:
                    if self._device.AckDown and callable(self._on_transmit):
                        self._on_transmit(TransmitStatus.TX_NETWORK_ACK)
                    if len(self._device.downlinkMacPayload) > 0 and callable(self._on_receive):
                        self._on_receive(ReceiveStatus.RX_OK, self._device.downlinkMacPayload)
                
                if self._Mac.answer is not None:
                    self.stack_transmit()


    def __increment_device_channel_group(self):
        self._device.channelGroup = (self._device.channelGroup + 1) % 8
        db = Database()
        db.open()
        db.update_channel_group(self._device.DevEUI.hex(), self._device.channelGroup)
        db.close()
        self._device.uplink_channel_min = self._region.value.UPLINK_CHANNEL_MIN + 8 * self._device.channelGroup
        self._device.uplink_channel_max = self._device.uplink_channel_min + 7 * (self._device.channelGroup + 1)
        if self._device.uplink_channel_max > self._region.value.UPLINK_CHANNEL_MAX:
            self._device.channelGroup = 0
            self._device.uplink_channel_min = self._region.value.UPLINK_CHANNEL_MIN
            self._device.uplink_channel_max = self._region.value.UPLINK_CHANNEL_MIN + 7

    def __random_channel(self) -> int:
        return random.randint(self._device.uplink_channel_min, self._device.uplink_channel_max)
    
    def __random_spreading_factor(self) -> int:
        return random.randint(self._region.value.SPREADING_FACTOR_MIN, self._region.value.SPREADING_FACTOR_MAX)
            

############################## API to LoRaRF Library
    def __radio_tx_mode(self):
        self._logger.debug(f"TX  : FREQ = {self._region.uplink_frequency(self._channel)} Hz, SF = {self._spreading_factor}")
        self._LoRa.setSyncWord(LORA_SYNC_WORD)
        self._LoRa.setTxPower(LORA_DEFAULT_TX_POWER, self._LoRa.TX_POWER_SX1262)
        self._LoRa.setFrequency(self._region.uplink_frequency(self._channel))
        self._LoRa.setLoRaModulation(self._spreading_factor, self._region.value.UPLINK_BANDWIDTH, LORA_CODING_RATE)
        self._LoRa.setLoRaPacket(self._LoRa.HEADER_EXPLICIT, LORA_PREAMBLE_SIZE, LORA_PAYLOAD_MAX_SIZE, UPLINK_CRC_TYPE, UPLINK_IQ_POLARITY)
    
    def __radio_rx1_mode(self):
        self._logger.debug(f"RX1 : FREQ = {self._region.downlink_frequency(self._channel)} Hz, SF = {self._spreading_factor}")
        #self._LoRa.purge(LORA_PAYLOAD_MAX_SIZE)
        self._LoRa.setSyncWord(LORA_SYNC_WORD)
        self._LoRa.setRxGain(self._LoRa.RX_GAIN_BOOSTED)
        self._LoRa.setFrequency(self._region.downlink_frequency(self._channel))
        self._LoRa.setLoRaModulation(self._spreading_factor, self._region.value.DOWNLINK_BANDWIDTH, LORA_CODING_RATE)
        self._LoRa.setLoRaPacket(self._LoRa.HEADER_EXPLICIT, LORA_PREAMBLE_SIZE, LORA_PAYLOAD_MAX_SIZE, DOWNLINK_CRC_TYPE, DOWNLINK_IQ_POLARITY)
        self._LoRa.request(self._LoRa.RX_CONTINUOUS)
        
    def __radio_rx2_mode(self)-> bool:
        self._logger.debug(f"RX2 : FREQ = {self._region.value.RX2_FREQUENCY} Hz, SF = {self._region.value.RX2_SPREADING_FACTOR}")
        #self._LoRa.purge(LORA_PAYLOAD_MAX_SIZE)
        self._LoRa.setSyncWord(LORA_SYNC_WORD)
        self._LoRa.setRxGain(self._LoRa.RX_GAIN_BOOSTED)
        self._LoRa.setFrequency(self._region.value.RX2_FREQUENCY)
        self._LoRa.setLoRaModulation(self._region.value.RX2_SPREADING_FACTOR, self._region.value.DOWNLINK_BANDWIDTH, LORA_CODING_RATE)
        self._LoRa.setLoRaPacket(self._LoRa.HEADER_EXPLICIT, LORA_PREAMBLE_SIZE, LORA_PAYLOAD_MAX_SIZE, DOWNLINK_CRC_TYPE, DOWNLINK_IQ_POLARITY)
        self._LoRa.request(self._LoRa.RX_CONTINUOUS)

    def __radio_transmit(self, delay:int)-> bool:
        self._LoRa.beginPacket()
        self._LoRa.write(list(self._device.uplinkPhyPayload), len(self._device.uplinkPhyPayload))
        self._LoRa.endPacket()
        self._logger.debug(f"UP  : PHYPAYLOAD = {self._device.uplinkPhyPayload.hex()}")
        time.sleep(delay - 0.6)
        self._LoRa.wait(0.1)
        return True

    def __radio_receive(self, delay:int)-> bytes:
        self._LoRa.wait()
        status = self._LoRa.status()
        if status == self._LoRa.STATUS_DEFAULT:
            # no IRQ
            self._LoRaIrqStatus = self._LoRa.STATUS_DEFAULT
            return bytes([])
        if status == self._LoRa.STATUS_TX_DONE:
            # TX_DONE IRQ
            if self._LoRaIrqStatus != self._LoRa.STATUS_TX_DONE:
                self._logger.debug(f"TX  : LoRa {RadioStatus(status)}")
                # Log is printed once
                self._LoRaIrqStatus = self._LoRa.STATUS_TX_DONE
            return bytes([])
        self._LoRaIrqStatus = status
        if status != self._LoRa.STATUS_RX_DONE:
            self._logger.warning(f"RX  : LoRa {RadioStatus(status)}")
            self._LoRa.clearDeviceErrors()
            self._LoRa.purge(self._LoRa.available())
            return bytes([])
        self._Mac.snr = self._LoRa.snr()
        self._Mac.rssi = self._LoRa.packetRssi()
        rx_length = self._LoRa.available()
        rx_bytes = self._LoRa.get(rx_length)
        self._logger.info(f"Rx bytes[{rx_length}]: {rx_bytes.hex()}")
        return rx_bytes
        
############################## API using LoRaMAC Wrapper Class to C Shared Library

    def __lorawan_message_type(self)->bool:
        try:
            self._device.message_type = WrapperLoRaMAC.message_type(self._device.downlinkPhyPayload)
            return True
        except:
            self._device.message_type = MessageType.PROPRIETARY
            self._logger.error(f"LoRaWAN : Message Type")
            return False

    def __lorawan_join_request(self) -> bool:
        try:
            self._device.DevNonce = random.randint(1, 65535)
            response = WrapperLoRaMAC.join_request(self._device.DevEUI, self._device.AppEUI, self._device.AppKey, self._device.DevNonce)
            db = Database()
            db.open()
            db.update_dev_nonce(self._device.DevEUI.hex(), self._device.DevNonce)
            db.close()
            if response["PHYPayload"] is None:
                self._logger.debug(f"LoRaWAN : JoinRequest Failed")
                return False
            self._device.uplinkPhyPayload = response["PHYPayload"]
            return True
        except:
            self._logger.error(f"LoRaWAN : Join Request")
            return False

    def __lorawan_join_accept(self) -> bool:
        try:
            response = WrapperLoRaMAC.join_accept(self._device.downlinkPhyPayload, self._device.AppKey, self._device.DevNonce)
            if response is None:
                self._logger.debug(f"LoRaWAN : JoinAccept Failed")
                return False
            self._device.isJoined = True
            self._device.DevAddr = bytes(response["DevAddr"])
            self._device.NwkSKey = bytes(response["NwkSKey"])
            self._device.AppSKey = bytes(response["AppSKey"])
            self._device.FCnt = 0
            db = Database()
            db.open()
            db.update_session_keys(self._device.DevEUI.hex(), self._device.DevAddr.hex(), 
                                        self._device.NwkSKey.hex(), self._device.AppSKey.hex())
            db.update_f_cnt(self._device.DevEUI.hex(), self._device.FCnt)
            db.close()
            return True
        except Exception as e:
            self._logger.error(f"LoRaWAN : Join Accept {e}")
            return False


    def __lorawan_data_up(self, confirmed:bool=False, fPort:int=None) -> bool:
        try:
            self._device.FCnt = self._device.FCnt + 1
            self._device.confirmed_uplink = confirmed
            if fPort is None:
                fPort = self._device.FPort
            if fPort is None:
                fPort = 0
            if not confirmed:
                response =  WrapperLoRaMAC.unconfirmed_data_up(self._device.uplinkMacPayload, self._device.FCnt, fPort, 
                                                            self._device.DevAddr, self._device.NwkSKey,self._device.AppSKey,
                                                            adr=False, ack=self._device.Ack, fOpts=self._Mac.answer)
            else:
                self._device.AckDown = False
                response =  WrapperLoRaMAC.confirmed_data_up(self._device.uplinkMacPayload, self._device.FCnt, fPort, 
                                                            self._device.DevAddr, self._device.NwkSKey,self._device.AppSKey,
                                                            adr=False, ack=self._device.Ack, fOpts=self._Mac.answer)
            db = Database()
            db.open()
            db.update_f_cnt(self._device.DevEUI.hex(), self._device.FCnt)
            db.close()
            if response["PHYPayload"] is None:
                self._logger.debug(f"LoRaWAN : Uplink Failed")
                return False
            
            self._device.uplinkPhyPayload = response["PHYPayload"]
            return True
        except:
            self._logger.error(f"LoRaWAN : Uplink")
            return False
    def __lorawan_data_down(self) -> bool:
        try:
            DevAddr = bytearray(self._device.downlinkPhyPayload[1:5])
            DevAddr.reverse()
            if int(DevAddr.hex(), 16) != int(self._device.DevAddr.hex(), 16):
                self._logger.debug(f"LoRaWAN : Unknown device data received")
                return False
            
            response = WrapperLoRaMAC.data_down(self._device.downlinkPhyPayload, self._device.DevAddr,
                                                self._device.NwkSKey, self._device.AppSKey)
            
            if response is None:
                return False
            if response["FOptsLen"] > 0:
                self._logger.debug(f"MAC command received")
                self._Mac.handle_mac_command(response["FOpts"])
            self._device.downlinkMacPayload = response["MacPayload"]
            self._device.Adr = response["ADR"]
            self._device.Rfu = response["RFU"]
            self._device.AckDown = response["ACK"]
            self._device.FCntDown = response["FCntDown"]
            self._device.FPortDown = response["FPortDown"]
            return True
        except:
            self._logger.error(f"LoRaWAN : Downlink")
            return False
