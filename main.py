from LoRaMAC import LoRaMAC
from LoRaMAC import Region
from LoRaMAC import Device
from LoRaMAC import JoinStatus, TransmitStatus, ReceiveStatus

import time
import logging


def on_join(status:JoinStatus):
	print(status)

def on_transmit(status:TransmitStatus):
	print(status)

def on_receive(status:ReceiveStatus, payload:bytes):
	print(status)
	if status == ReceiveStatus.RX_OK:
		print("Receive Data = ", list(payload))

KEYS = {
    "DevEUI" : "1d42fbec13160990",
    "AppEUI" : "1d42fbec13160990",
    "AppKey" : "4fe6e906d37fd200f25f82f7df6ba0dd"
}



if __name__ == "__main__":
	device = Device(KEYS["DevEUI"], KEYS["AppEUI"], KEYS["AppKey"])
	LoRaWAN = LoRaMAC(device, Region.US915)
	LoRaWAN.set_logging_level(logging.DEBUG)
	LoRaWAN.set_callback(on_join, on_transmit, on_receive)
	LoRaWAN.join(max_tries=3, forced=True)
	while True:
		if LoRaWAN.is_joined():
			LoRaWAN.transmit(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x6, 0x07, 0x08, 0x09]), True)
		time.sleep(5)	
