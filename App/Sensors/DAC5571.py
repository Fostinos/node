

import smbus

class DAC5571():

    VOLTAGE_MIN = 0.0
    VOLTAGE_MAX = 3.3
    DAC_RESOLUTION = 4095

    ADDRESS_DAC_1 = 0x60
    ADDRESS_DAC_2 = 0x61

    def __init__(self, address:int, busId:int=1):
        self.__busId = busId
        self.__address = address
        self.__smbus = smbus.SMBus(self.__busId) 


    def set_voltage(self, voltage:float)->bool:
        """
        Sets the output voltage of the DAC5571.
        Args:
            voltage (float): The voltage to set (between 0.0 and 3.3).
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            if voltage < DAC5571.VOLTAGE_MIN:
                return False
            if voltage > DAC5571.VOLTAGE_MAX:
                return False

            dac_value = int((voltage / DAC5571.VOLTAGE_MAX) * DAC5571.DAC_RESOLUTION)

            formated_data = [(dac_value >> 4) & 0xFF, (dac_value << 4) & 0xFF]
            self.__smbus.write_i2c_block_data(self.__address, 0x40, formated_data)
            return True
        except:
            return False
        