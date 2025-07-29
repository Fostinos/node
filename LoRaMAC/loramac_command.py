

from enum import IntEnum
from .loramac_region import Region
import logging

class CID(IntEnum):
    LinkCheck     = 0x02
    LinkADR       = 0x03
    DutyCycle     = 0x04
    RXParamSetup  = 0x05
    DevStatus     = 0x06
    NewChannel    = 0x07
    RXTimingSetup = 0x08
    TXParamSetup  = 0x09
    DlChannel     = 0x0A
    DeviceTime    = 0x0B

class LinkADR:

    def __init__(self, dr:int, tx_pwr:int, ch_mask:int, ch_mask_ctrl:int, nb_tx:int):
        self.data_rate = dr
        self.tx_power = tx_pwr
        self.ch_mask = ch_mask
        self.ch_mask_ctrl = ch_mask_ctrl
        self.nb_tx = nb_tx

class DutyCycle:
    pass


class MacCommand():

    def __init__(self, region:Region=Region.US915):
        if region == Region.US915:
            self.link_adr = LinkADR(3, 21, 0, 1, 1)
        elif region == Region.EU868:
            self.link_adr = LinkADR(3, 14, 0, 1, 1)
        self.answer:bytes = None
        self.battery_level:int = 0  
        self.snr:float = 0
        self.rssi:float = 0
        self._region = region
        self._logger = logging.getLogger("APP[LoRaMAC]")
        pass
        
    def __LinkADRAns(self, LinkADRReq:list):
        if len(LinkADRReq) != 4:
            self._logger.debug(f"Incorrect LinkADRReq: {bytes(LinkADRReq).hex()}")
        # To be implemented for ADR
        PowerACK = 1
        DataRateACK = 1
        ChannelMaskACK = 1
        LinkADRAns = [CID.LinkADR]
        LinkADRAns.append(0x00 | (PowerACK << 2) | (DataRateACK << 1) | (ChannelMaskACK << 0))
        if self.answer is None:
            self.answer = bytearray([])
        self.answer = self.answer + bytes(LinkADRAns)
        self.answer = bytes(self.answer)
        self._logger.debug(f"LinkADRAns Response: {self.answer.hex()}")

    def __DevStatusAns(self):
        # To be implemented for ADR
        DevStatusAns = [CID.DevStatus]
        DevStatusAns.append(self.battery_level)
        snr = max(-32, min(31, int(self.snr)))
        snr_encoded = snr & 0x3F           # Get two's complement 6-bit representation
        DevStatusAns.append(self.battery_level)
        DevStatusAns.append(snr_encoded)
        if self.answer is None:
            self.answer = bytearray([])
        self.answer = self.answer + bytes(DevStatusAns)
        self.answer = bytes(self.answer)
        self._logger.debug(f"DevStatusAns Response: {self.answer.hex()}")

    def __DutyCycleAns(self, DutyCycleReq:list)->bytes:
        pass
        
    def handle_mac_command(self, fOpts:bytes):
        mac_cmd = list(fOpts)
        index = 0
        cid = 0
        size = len(mac_cmd)
        self._logger.info(f"MAC cmd[{size}] = {fOpts.hex()}")
        while index < size:
            cid = mac_cmd[index]
            if cid == CID.LinkADR:
                self._logger.debug(f"Received LinkADRReq Command")
                self.__LinkADRAns(mac_cmd[index:index+4])
                index = index + 4
            if cid == CID.DevStatus:
                self._logger.debug(f"Received LinkADRReq Command")
                self.__DevStatusAns()
            index = index + 1