


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
	LOW     = 0
	HIGH    = 1



class PCF8574():
	
	TOTAL_PIN = 8

	def __init__(self, address:int=0x20, busId:int=1):
		self.__busId = busId
		self.__address = address
		self.__smbus = smbus.SMBus(self.__busId)
		self.__pin_states = [PinState.LOW] * PCF8574.TOTAL_PIN
		self.__smbus.write_byte(self.__address, 0x00)

	def write(self, pin:GPIO, state:PinState)->bool:
		"""
		Writes the state to a specific pin.
		Args:
			pin (GPIO): The pin to write to.
			state (PinState): The state to set the pin to.
		Returns:
			bool: True if the write operation was successful, False otherwise.
		"""
		old_pin_state = -1
		try:
			data = 0x00
			old_pin_state = self.__pin_states[pin]
			self.__pin_states[pin] = state
			for pin_number, pin_state in enumerate(self.__pin_states):
				if pin_state:
					data = data +  2**pin_number
			self.__smbus.write_byte(self.__address, data)
			return True
		except:
			# If an error occurs, revert the pin state
			if old_pin_state != -1:
				self.__pin_states[pin] = old_pin_state
			return False

	def read(self, pin:GPIO)->PinState:
		"""
		Reads the state of a specific pin from the PCF8574 sensor.
		Args:
			pin (GPIO): The pin to read from.
		Returns:
			PinState: The state of the pin (LOW or HIGH).
		"""
		try:
			data = self.__smbus.read_byte(self.__address)
			data = data >> pin
			data = data & 1
			return PinState(data)
		except:
			return -1

	
	def get_pin_states_from_driver(self)->list[PinState]:
		"""
		Reads the state of all pins from the PCF8574 internal driver.\n
		Please use it with caution: recommended method `get_pin_states_from_sensor()` 
		Returns:
			list[PinState]: A list of PinState representing the state of each pin, empty list if an error occurs.
		"""
		try:
			return self.__pin_states
		except:
			return []

	def get_pin_states_from_sensor(self)->list[PinState]:
		""""
		Reads the state of all pins from the PCF8574 sensor.
		Returns:
			list[PinState]: A list of PinState representing the state of each pin, empty list if an error occurs.
		"""
		try:
			data = self.__smbus.read_byte(self.__address)
			for pin in range(PCF8574.TOTAL_PIN):
				pin_data = data >> pin
				self.__pin_states[pin] = PinState(pin_data & 1)
			return self.__pin_states
		except:
			return []