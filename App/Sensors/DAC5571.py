

import smbus

class DAC5571():

    VOLTAGE_MIN = 0.0
    VOLTAGE_MAX = 3.3
    DAC_RESOLUTION = 4095

    def __init__(self, busId:int=1, address:int=0x00):
        self.__busId = busId
        self.__address = address
        self.__smbus = smbus.SMBus(self.__busId) 
        pass


    def set_voltage(self, voltage:float)->bool:
        try:
            if voltage > DAC5571.VOLTAGE_MAX:
                voltage = DAC5571.VOLTAGE_MAX
            elif voltage < DAC5571.VOLTAGE_MIN:
                voltage = DAC5571.VOLTAGE_MIN

            dac_value = int((voltage / DAC5571.VOLTAGE_MAX) * DAC5571.DAC_RESOLUTION)

            formated_data = [(dac_value >> 4) & 0xFF, (dac_value << 4) & 0xFF]
            self.__smbus.write_i2c_block_data(self.__address, 0x40, formated_data)
            return True
        except:
            return False
        

class MCP4725():
    
    def __init__(self, address:int=0x49):
        self.__dac = DAC5571(address=address)
        self.__address = address
    

    def set_voltage(self, voltage:float)->bool:
        return self.__dac.set_voltage(voltage)