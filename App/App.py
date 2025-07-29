from LoRaMAC import LoRaMAC
from LoRaMAC import Region
from LoRaMAC import Device
from LoRaMAC import JoinStatus, TransmitStatus, ReceiveStatus

import os
import json
import time
import logging

from .Sensors import Relay, DAC5571
from .Sensors import PCF8574, GPIO, PinState

CONFIG_NAME          = "config"
RELAY_CONTROL_NAME   = "RelayControl"
RELAY_THRESHOLD_NAME = "RelayThresholds"
UPLINK_INTERVAL_NAME = "UplinkInterval"


class App():
    """
    Represents an application using the LoRaMAC protocol.

    Attributes:
        __logger (logging.Logger): The logger object for logging messages.
        __region (Region): The region of the LoRaWAN network.
        __device (Device): The device object representing the application's device.
        __LoRaWAN (LoRaMAC): The LoRaMAC object for handling LoRaWAN communication.
    """
    
    VOLTAGE_RESOLUTION         = 1000
    LORAWAN_REJOIN_INTERVAL    = 86400 # 1 day (rejoin network after 1 day to renew session keys and frame counters)
    DELAY_PER_LOOP             = 0.1

    RELAY_CONTROL_MANUAL       = 0x00
    RELAY_CONTROL_AUTOMATIC    = 0x01

    CMD_FAILURE                = 0x00
    CMD_SUCCESS                = 0x01

    APP_CHANNEL                = 0xFF

    TYPE_TIMESTAMP             = 0x00
    TYPE_RELAY                 = 0x01

    TYPE_DAC_1                 = 0xA1
    TYPE_DAC_2                 = 0xA2
    
    TYPE_UPLINK_INTERVAL       = 0xB1
    TYPE_RELAY_CONTROL         = 0xB2
    TYPE_RELAY_THRESHOLDS      = 0xB3
    TYPE_READ_RELAY_THRESHOLDS = 0xB4

    TYPE_PIN_0                 = 0xF0
    TYPE_PIN_1                 = 0xF1
    TYPE_PIN_2                 = 0xF2
    TYPE_PIN_3                 = 0xF3
    TYPE_PIN_4                 = 0xF4
    TYPE_PIN_5                 = 0xF5
    TYPE_PIN_6                 = 0xF6
    TYPE_PIN_7                 = 0xF7
    TYPE_READ_PIN_STATES       = 0xF8

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
        self.__last_rejoin_timestamp = 0
        self.__last_transmit_timestamp = 0
        self.__relay1 = Relay(address=Relay.ADDRESS_RELAY_1)
        self.__relay2 = Relay(address=Relay.ADDRESS_RELAY_2)
        self.__port = PCF8574()
        self.__dac1 = DAC5571(address=DAC5571.ADDRESS_DAC_1)
        self.__dac2 = DAC5571(address=DAC5571.ADDRESS_DAC_2)
        self.__adc_channels = [0]*self.__port.TOTAL_PIN
        self.__logger.info(f"App Initialized")

        
        self.__handlers = {
            App.TYPE_UPLINK_INTERVAL: {
                "data_size": 4,
                "handler": self.__handle_downlink_uplink_interval,
                "response": None
            },
            App.TYPE_RELAY_CONTROL:{
                "data_size": 1,
                "handler": self.__handle_downlink_relay_control,
                "response": None
            },
            App.TYPE_RELAY_THRESHOLDS: {
                "data_size": 16,
                "handler": self.__handle_downlink_config_relay_thresholds,
                "response": self.__read_relay_thresholds
            },
            App.TYPE_DAC_1:  {
                "data_size": 2,
                "handler": self.__handle_downlink_dac_1,
                "response": None
            },
            App.TYPE_DAC_2:  {
                "data_size": 2,
                "handler": self.__handle_downlink_dac_2,
                "response": None
            },
        }

    def run(self):
        """
        Runs The `App` continuously
        """
        self.__logger.info(f"App Running")
        self.__last_rejoin_timestamp = time.time()
        self.__LoRaWAN.join(max_tries=3, forced=True)

        while True:

            # Rejoin the network every day
            if time.time() > (self.__last_rejoin_timestamp + App.LORAWAN_REJOIN_INTERVAL):
                self.__last_rejoin_timestamp = time.time()
                self.__LoRaWAN.join(max_tries=3, forced=True)

            self.__read_channels()
            self.__auto_processing()

            if not self.__LoRaWAN.is_joined():
                time.sleep(1)
                continue

            if (time.time() + App.DELAY_PER_LOOP) > (self.__last_transmit_timestamp + \
                                                     self.__config[CONFIG_NAME][UPLINK_INTERVAL_NAME]):
                self.__last_transmit_timestamp = time.time()
                self.__logger.info("The device transmits data")
                data = bytearray([App.APP_CHANNEL, App.TYPE_TIMESTAMP])
                data = data + int(self.__last_transmit_timestamp).to_bytes(4, byteorder='big', signed=False)
                data = data + bytearray([App.APP_CHANNEL, App.TYPE_RELAY])
                for voltage in self.__adc_channels:
                    data = data + int(voltage * App.VOLTAGE_RESOLUTION).to_bytes(2, byteorder='big', signed=False)
                pin_states_data = self.__read_pin_states_from_sensor()
                if pin_states_data is None:
                    pin_states_data = self.__read_pin_states_from_driver()
                if pin_states_data is not None:
                    data = data + pin_states_data
                self.__LoRaWAN.transmit(bytes(data))
                time.sleep(1)
            
            # minimum delay (!important)
            time.sleep(App.DELAY_PER_LOOP)

    def __read_channels(self):
        for i in range(self.__port.TOTAL_PIN):
            if i < 4:
                self.__adc_channels[i] = self.__relay1.read_voltage(i%4)
            else:
                self.__adc_channels[i] = self.__relay2.read_voltage(i%4)

    def __auto_processing(self):
        if not self.__config[CONFIG_NAME][RELAY_CONTROL_NAME]:
            return
        thresholds = self.__config[CONFIG_NAME][RELAY_THRESHOLD_NAME]
        pin = 0
        for channel in self.__adc_channels:
            if channel > thresholds[pin]:
                self.__port.write(GPIO(pin), PinState.LOW)
            else:
                self.__port.write(GPIO(pin), PinState.HIGH)
            pin = pin + 1
            


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
            self.__logger.error(f"Save configuration file")
            return False
        
########################## Downlink commands handler 
    
    def __handle_downlink(self, payload:bytes):
        cmd = list(payload)
        size = len(cmd)
        index = 0
        cmd_type = 0xFF
        cmd_state = False
        cmd_response = None
        response_payload = bytearray([])
        while index < size:
            
            if index + 1 >= size:
                break # Not enough bytes left for CHANNEL and TYPE

            if cmd[index] != App.APP_CHANNEL:
                index = index + 1
                # Skip unknown channel
                continue

            index = index + 1
            if index >= size:
                break  # No TYPE byte
            cmd_type = cmd[index]
            index = index + 1

            cmd_response = None
            if cmd_type in self.__handlers:
                cmd_config = self.__handlers[cmd_type]
                if cmd_config is None:
                    break
                cmd_data_size = cmd_config.get("data_size", None)
                if cmd_data_size is None:
                    break
                cmd_handler = cmd_config.get("handler", None)
                if cmd_handler is None or not callable(cmd_handler):
                    break
                if index + cmd_data_size > size:
                    break  # Not enough data for this command
                # Execute the cmd
                cmd_state = cmd_handler(cmd, index)
                if cmd_state is False:
                    break
                # Go to the next cmd
                index = index + cmd_data_size
                cmd_response_cb = cmd_config.get("response", None)
                if cmd_response is not None and callable(cmd_response_cb):
                    cmd_response = cmd_response_cb()
                if cmd_response is not None:
                    response_payload = response_payload + cmd_response


            
            elif cmd_type >= App.TYPE_PIN_0 and cmd_type <= App.TYPE_PIN_7:
                pin_not_verified = cmd_type - App.TYPE_PIN_0
                cmd_state = self.__handle_downlink_write_pin_state(cmd, index, pin_not_verified)
                if cmd_state is False:
                    break
                # Go to the next cmd
                index = index + 1
            
            elif cmd_type == App.TYPE_READ_PIN_STATES:
                cmd_response = self.__handle_downlink_read_pin_states()
                if cmd_response is None:
                    cmd_state = False
                    break
                
                cmd_state = True
                response_payload = response_payload + cmd_response
                # Go to the next cmd
                index = index + 1
            
            elif cmd_type == App.TYPE_READ_RELAY_THRESHOLDS:
                cmd_response = self.__handle_downlink_read_relay_thresholds()
                if cmd_response is None:
                    cmd_state = False
                    break
                
                cmd_state = True
                response_payload = response_payload + cmd_response
                # Go to the next cmd
                index = index + 1
        
        if cmd_state is True:
            self.__logger.info(f'CMD_SUCCESS')
            self.__LoRaWAN.transmit(bytes([App.CMD_SUCCESS]))
        else:
            self.__logger.warning(f'CMD_FAILURE')
            self.__LoRaWAN.transmit(bytes([App.CMD_FAILURE]))
        
        if len(response_payload) > 0:
            self.__LoRaWAN.transmit(bytes(response_payload))

    def __get_uint32_from_command(self, cmd:list, index:int)->int:
            if index + 3 >= len(cmd): 
                return None
            integer_bytes = bytes([cmd[index], cmd[index+1], cmd[index+2], cmd[index+3]])
            return int.from_bytes(integer_bytes)
    
    def __get_uint16_from_command(self, cmd:list, index:int)->int:
            if index + 1 >= len(cmd): 
                return None
            integer_bytes = bytes([cmd[index], cmd[index+1]])
            return int.from_bytes(integer_bytes)

    def __handle_downlink_uplink_interval(self, cmd:list, index:int)->bool:
        try:
            interval = self.__get_uint32_from_command(cmd, index)
            if interval is None: 
                return False
            old_interval = self.__config[CONFIG_NAME][UPLINK_INTERVAL_NAME]
            self.__config[CONFIG_NAME][UPLINK_INTERVAL_NAME] = interval
            if self.__save_config():
                return True
            else: # restore old interval
                self.__config[CONFIG_NAME][UPLINK_INTERVAL_NAME] = old_interval
                return False
        except:
            return False
    
    def __handle_downlink_relay_control(self, cmd:list, index:int)->bool:
        try:
            if index >= len(cmd): 
                return False
            control = cmd[index]
            if control == App.RELAY_CONTROL_MANUAL:
                control = False
            elif control == App.RELAY_CONTROL_AUTOMATIC:
                control = True
            else:
                return False
            old_control = self.__config[CONFIG_NAME][RELAY_CONTROL_NAME]
            self.__config[CONFIG_NAME][RELAY_CONTROL_NAME] = control
            if self.__save_config():
                return True
            else: # restore old control
                self.__config[CONFIG_NAME][RELAY_CONTROL_NAME] = old_control
                return False
        except:
            return False
    
    def __handle_downlink_config_relay_thresholds(self, cmd:list, index:int)->bool:
        try:
            thresholds = []
            for i in range(self.__port.TOTAL_PIN):
                integer = self.__get_uint16_from_command(cmd, index)
                index = index + 2
                if integer is None:
                    return False
                thresholds.append(float(integer) / App.VOLTAGE_RESOLUTION)
            old_thresholds = self.__config[CONFIG_NAME][RELAY_THRESHOLD_NAME]
            self.__config[CONFIG_NAME][RELAY_THRESHOLD_NAME] = thresholds
            if self.__save_config():
                return True
            else: # restore old interval
                self.__config[CONFIG_NAME][RELAY_THRESHOLD_NAME] = old_thresholds
                return False
        except:
            return False
    
    def __handle_downlink_dac_1(self, cmd:list, index:int)->bool:
        try:
            integer = self.__get_uint16_from_command(cmd, index)
            if integer is None: 
                return False
            dac_value = float(integer) / App.VOLTAGE_RESOLUTION
            return self.__dac1.set_voltage(dac_value)
        except:
            return False
    
    def __handle_downlink_dac_2(self, cmd:list, index:int)->bool:
        try:
            integer = self.__get_uint16_from_command(cmd, index)
            if integer is None: 
                return False
            dac_value = float(integer) / App.VOLTAGE_RESOLUTION
            return self.__dac2.set_voltage(dac_value)
        except:
            return False
    
    def __handle_downlink_write_pin_state(self, cmd:list, index:int, pin_not_verified:int)->bool:
        try:
            if index > len(cmd):
                return False
            state_not_verified = cmd[index]
            if pin_not_verified < GPIO.PIN_0 or pin_not_verified > GPIO.PIN_7:
                return False
            pin = GPIO(pin_not_verified)
            if state_not_verified != PinState.LOW and state_not_verified != PinState.HIGH:
                return False
            state = PinState(state_not_verified)
            return self.__port.write(pin, state)
        except:
            return False
        
    def __handle_downlink_read_pin_states(self)->bytes:
        try:
            data = self.__read_pin_states_from_sensor()
            if data is not None:
                return data
            return self.__read_pin_states_from_driver()
        except:
            return None
        
        
    def __handle_downlink_read_relay_thresholds(self)->bytes:
        return self.__read_relay_thresholds()
        
    def __read_relay_thresholds(self)->bytes:
        try:
            data = bytearray([App.APP_CHANNEL, App.TYPE_READ_RELAY_THRESHOLDS])
            thresholds = list(self.__config[CONFIG_NAME][RELAY_THRESHOLD_NAME])
            for threshold in thresholds:
                data = data + int(threshold * App.VOLTAGE_RESOLUTION).to_bytes(2, byteorder='big', signed=False)
            return bytes(data)
        except:
            return None


    def __read_pin_states_from_sensor(self)->bytes:
        """
        Reads digital pin states from the sensor and formats them for uplink transmission.

        Returns:
            bytes: Formatted bytes for uplink (channel, type, 8 pin states)
            None: If an error occurs or no pin states are available
        """
        try:
            data = bytearray([App.APP_CHANNEL, App.TYPE_READ_PIN_STATES])
            pin_states = self.__port.get_pin_states_from_sensor()
            if len(pin_states) == 0:
                return None
            pins_data = []
            for pin_state in pin_states:
                pins_data.append(pin_state.value)
            data = data + bytearray(pins_data)
            return bytes(data)
        except:
            return None

    def __read_pin_states_from_driver(self)->bytes:
        """
        Reads digital pin states from the internal driver and formats them for uplink transmission.

        Returns:
            bytes: Formatted bytes for uplink (channel, type, 8 pin states)
            None: If an error occurs or no pin states are available
        """
        try:
            data = bytearray([App.APP_CHANNEL, App.TYPE_READ_PIN_STATES])
            pin_states = self.__port.get_pin_states_from_driver()
            if len(pin_states) == 0:
                return None
            pins_data = []
            for pin_state in pin_states:
                pins_data.append(pin_state.value)
            data = data + bytearray(pins_data)
            return bytes(data)
        except:
            return None

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
        else:
            self.__LoRaWAN.join(max_tries=3, forced=True)

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
            self.__handle_downlink(payload)