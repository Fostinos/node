

from enum import IntEnum

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


class MacCommand():

    def __init__(self):
        self.answer:bytes = None
        pass
        
    def __LinkADRAns(self, LinkADRReq:list):
        PowerACK = 1
        DataRateACK = 1
        ChannelMaskACK = 1
        LinkADRAns = [CID.LinkADR]
        LinkADRAns.append(0x00 | (PowerACK << 2) | (DataRateACK << 1) | (ChannelMaskACK << 0))
        self.answer = bytes(LinkADRAns)

    def __DutyCycleAns(self, DutyCycleReq:list)->bytes:
        pass
        
    def handle_mac_command(self, fOpts:bytes):
        mac_cmd = list(fOpts)
        index = 0
        cid = 0
        size = len(mac_cmd)
        while index < size:
            cid = mac_cmd[index]
            if cid == CID.LinkADR:
                self.__LinkADRAns(mac_cmd[index:index+4])
                index = index + 4
            index = index + 1