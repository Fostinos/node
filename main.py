

from LoRaMAC import Region
from App import App

import logging

APP = App(Region.US915, logging.DEBUG)

if __name__ == "__main__":
	APP.run()
