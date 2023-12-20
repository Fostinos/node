


import smbus
from enum import IntEnum


class GPIO(IntEnum):
	PIN_0   = 0
	PIN_1   = 1
	PIN_2   = 2
	PIN_3   = 3
	PIN_4   = 4
	PIN_5   = 5
	PIN_6   = 6
	PIN_7   = 7


class PinState(IntEnum):
	LOW     = 1
	HIGH    = 0



class PCF8574():
	
	TOTAL_PIN = 8

	def __init__(self, address:int=0x20, busId:int=1):
		self.__busId = busId
		self.__address = address
		self.__smbus = smbus.SMBus(self.__busId)
		self.__pin_states = [0] * PCF8574.TOTAL_PIN
		self.__smbus.write_byte(self.__address, 0x00)

	def write(self, pin:GPIO, state:PinState)->bool:
		try:
			data = 0x00
			self.__pin_states[pin] = state
			for pin_number, pin_state in enumerate(self.__pin_states):
				if pin_state == 1:
					data = data +  2**pin_number
			self.__smbus.write_byte(self.__address, data)
			return True
		except:
			return False

	def read(self, pin:GPIO)->PinState:
		try:
			data = self.__smbus.read_byte(self.__address)
			data = data >> pin
			data = data & 1
			return PinState(data)
		except:
			return -1