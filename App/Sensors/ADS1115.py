# Registers in the ADS1115
DEVICE_REG_CONVERSION	= 0x00
DEVICE_REG_CONFIG 		= 0x01
DEVICE_REG_LO_THRESH	= 0x02
DEVICE_REG_HI_THRESH 	= 0x03

# Configuration register fields

# Operational Status
CONFIG_OS		 				= 0X8000
CONFIG_OS_START 				= 0X8000
CONFIG_OS_PERFORMING_CONVERSION	= 0X0000
CONFIG_OS_NOT_PERFORMING_OPERATION= 0X8000

# Differential measurements
CONFIG_MUX_AIN0P_AIN1N			= 0X0000 # (default)
CONFIG_MUX_AIN1P_AIN3N			= 0X1000
CONFIG_MUX_AIN2P_AIN3N			= 0X2000
CONFIG_MUX_AIN3P_AIN3N			= 0X3000
# Single ended measurements
CONFIG_MUX_AIN0P_GNDN			= 0X4000 
CONFIG_MUX_AIN1P_GNDN			= 0X5000
CONFIG_MUX_AIN2P_GNDN			= 0X6000
CONFIG_MUX_AIN3P_GNDN			= 0X7000

# Programmable gain amplifier configuration
CONFIG_FSR_6V144 				= 0X0000
CONFIG_FSR_4V096 				= 0X0200
CONFIG_FSR_2V048 				= 0X0400 # (default)
CONFIG_FSR_1V024 				= 0X0600
CONFIG_FSR_0V512 				= 0X0800
CONFIG_FSR_0V256 				= 0X0A00
CONFIG_FSR_0V256 				= 0X0C00
CONFIG_FSR_0V256 				= 0X0E00

# Continuous or single shot mode
CONFIG_MODE_CONTINUOUS 			= 0X0000
CONFIG_MODE_SINGLE_SHOT 		= 0X0100 # (default)

# Data rate
CONFIG_DATA_RATE_8SPS			= 0X0000
CONFIG_DATA_RATE_16SPS			= 0X0020
CONFIG_DATA_RATE_32SPS			= 0X0040
CONFIG_DATA_RATE_64SPS			= 0X0060
CONFIG_DATA_RATE_128SPS			= 0X0080 #(default)
CONFIG_DATA_RATE_2508SPS		= 0X00A0
CONFIG_DATA_RATE_475SPS			= 0X00C0
CONFIG_DATA_RATE_860SPS			= 0X00E0

# Comparitor mode
CONFIG_COMP_MODE_TRADITIONAL	= 0X0000 #(default)
CONFIG_COMP_MODE_WINDOW 		= 0X0010

# Comparitor polarity
CONFIG_COMP_POL_ACTIVE_LOW 		= 0X0000 #(default)
CONFIG_COMP_POL_ACTIVE_HIGH		= 0X0008

# Comparitor latching
CONFIG_COMP_LAT 				= 0X0004
CONFIG_COMP_LAT_NON_LATCHING	= 0X0000 #(default)
CONFIG_COMP_LAT_LATCHING 		= 0X0004

# comparitor queue and disable
CONFIG_COMP_QUE 				= 0X0003
CONFIG_COMP_QUE_1_CONV 			= 0X0000
CONFIG_COMP_QUE_2_CONV 			= 0X0001
CONFIG_COMP_QUE_4_CONV 			= 0X0002
CONFIG_COMP_QUE_DISABLE 		= 0X0003 #(default)


import smbus


class ADS1115():
    
	ADC_RESOLUTION = 32767.0
	GAIN = 4.096

	def __init__(self, address:int=0x00, busId:int=1):
		self.__cmd = None
		self.__busId = busId
		self.__address = address
		self.__smbus = bus = smbus.SMBus(self.__busId)


	def read_channel(self, channel:int=0)->float:
		try:
			if channel < 0 or channel > 3:
				return -1.0
			self.__build_read_command(channel)
			self.__send_command()
			self.__wait()
			return self.__read_adc_value()
		except:
			return -2.0


	def __read_adc_value(self)->float:
		# read result (note byte swap)
		result = self.__swap(self.__smbus.read_word_data(self.__address, DEVICE_REG_CONVERSION))
		return (result/ADS1115.ADC_RESOLUTION) * ADS1115.GAIN

	def __wait(self):
		# wait for conversion to complete (blocking)
		while True:
			status = self.__swap(self.__smbus.read_word_data(self.__address, DEVICE_REG_CONFIG))
			if (status & CONFIG_OS) != CONFIG_OS_PERFORMING_CONVERSION:
				break

	def __swap(self, a):
		return ((a&0xff00)>>8) | ((a&0x00ff)<<8)

	def __build_read_command(self, channel):
		# Build read command
		self.__cmd = (
				CONFIG_OS_START +				# start conversion 
				CONFIG_MUX_AIN0P_GNDN  + 		# single ended conversion
				(channel<<12) + 				# select channel
				CONFIG_FSR_4V096 + 				# 4.096v pre amp (3.3v signal)
				CONFIG_MODE_SINGLE_SHOT + 		# single conversion and shutdown
				CONFIG_DATA_RATE_128SPS + 		# data rate
				CONFIG_COMP_MODE_TRADITIONAL + 	# comp conventional 
				CONFIG_COMP_POL_ACTIVE_LOW + 	# comp active low
				CONFIG_COMP_LAT_NON_LATCHING + 	# comp non latching
				CONFIG_COMP_QUE_DISABLE         # comp disabled
			)
	
	def __send_command(self):
		#send read command (note byte swap)
		config =  self.__swap(self.__cmd)
		self.__smbus.write_word_data(self.__address, DEVICE_REG_CONFIG, config)



class Relay():

	ADC_FACTOR = 3.025
	
	def __init__(self, address:int=0x49):
		self.__adc = ADS1115(address=address)
		self.__address = address
	

	def read_voltage(self, channel:int)->float:
		return self.__adc.read_channel(channel) * Relay.ADC_FACTOR
	


class Banana():

	ADC_FACTOR = 3.025
	
	def __init__(self, address:int=0x48):
		self.__adc = ADS1115(address=address)
		self.__address = address
	

	def read_voltage(self, channel:int)->float:
		return self.__adc.read_channel(channel) * Banana.ADC_FACTOR