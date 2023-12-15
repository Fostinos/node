from .loramac_functions import messageType, joinRequest,joinAccept, unconfirmedDataUp, confirmedDataUp, dataDown
from .loramac_types import *
import ctypes

class WrapperLoRaMAC :
    """LoRaMAC Wrapper Class to C Shared Library"""

    LORAWAN_MAX_FOPTS_LEN = 15
    LORAWAN_BUFFER_SIZE_MAX = 224

    @staticmethod
    def message_type(PHYPayload:bytes) -> MessageType :

        phyPayload = bytes(PHYPayload)

        bufferSize = len(phyPayload)
        buffer = (ctypes.c_uint8 * bufferSize)()
        ctypes.memmove(ctypes.addressof(buffer), phyPayload, bufferSize)

        msg_type : MHDR_MType_t = messageType(buffer, bufferSize)

        return MessageType(msg_type.value)


    @staticmethod
    def join_request(DevEUI:bytes, AppEUI:bytes, AppKey:bytes, DevNonce:int) -> dict :

        devEUI = tuple(DevEUI)
        appEUI = tuple(AppEUI)
        appKey = tuple(AppKey)

        join = JoinRequest_t(devEUI, appEUI, appKey, DevNonce)
        buffer = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX)()
        bufferSize = WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX

        length = joinRequest(ctypes.byref(join), buffer, bufferSize)

        output = {}
        PHYPayload = []
        for i in range(length):
            PHYPayload.append(buffer[i])
        output["PHYPayload"] = bytes(PHYPayload)

        return output
    
    
    @staticmethod
    def join_accept(PHYPayload:bytes, AppKey:bytes, DevNonce:int) -> dict :

        phyPayload = bytes(PHYPayload)
        appKey = tuple(AppKey)

        DLsettings_data = DLsettings_t(0, 0, False)
        FreqCH4 = (ctypes.c_uint8 * 3)()
        FreqCH5 = (ctypes.c_uint8 * 3)()
        FreqCH6 = (ctypes.c_uint8 * 3)()
        FreqCH7 = (ctypes.c_uint8 * 3)()
        FreqCH8 = (ctypes.c_uint8 * 3)()
        CFlist_data = CFlist_t(FreqCH4, FreqCH5, FreqCH6, FreqCH7, FreqCH8)
        AppNonce = 0
        NetID = 0
        DevAddr = 0
        RxDelay = 0
        hasCFlist = False
        NwkSKey = (ctypes.c_uint8 * 16)()
        AppSKey = (ctypes.c_uint8 * 16)()
        join = JoinAccept_t(AppNonce, NetID, DevAddr, DLsettings_data, RxDelay, CFlist_data, hasCFlist, DevNonce, appKey, NwkSKey, AppSKey)

        bufferSize = len(phyPayload)
        buffer = (ctypes.c_uint8 * bufferSize)()
        ctypes.memmove(ctypes.addressof(buffer), phyPayload, bufferSize)

        status = joinAccept(ctypes.byref(join), buffer, bufferSize)

        if status == False:
            return None

        output = {}
        output["DevAddr"] = bytes.fromhex(hex(join.DevAddr)[2:].zfill(8))
        NwkSKey = []
        AppSKey = []
        for i in range(16):
            NwkSKey.append(join.NwkSKey[i])
            AppSKey.append(join.AppSKey[i])

        output["NwkSKey"] = bytes(NwkSKey)
        output["AppSKey"] = bytes(AppSKey)

        return output
    

    @staticmethod
    def unconfirmed_data_up(MacPayload:bytes, FCnt:int, FPort:int, DevAddr:bytes, NwkSKey:bytes, AppSKey:bytes, adr:bool=True, ack:bool=False) -> dict:

        payload = tuple(MacPayload)
        nwkSKey = tuple(NwkSKey)
        appSKey = tuple(AppSKey)

        FHDR_FCtrl_uplink_data = FHDR_FCtrl_uplink_t(adr, False, ack, False, 0)
        FHDR_FCtrl_data = FHDR_FCtrl_t((),FHDR_FCtrl_uplink_data)
        FOpts = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_MAX_FOPTS_LEN)()

        FHDR_data = FHDR_t(int(DevAddr.hex(), 16), FHDR_FCtrl_data, FCnt, FOpts)

        mac = MACPayload_t(FHDR_data, nwkSKey, appSKey, FPort, len(payload), payload)
        buffer = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX)()
        bufferSize = WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX

        length = unconfirmedDataUp(ctypes.byref(mac), buffer, bufferSize)
    
        output = {}
        PHYPayload = []
        for i in range(length):
            PHYPayload.append(buffer[i])
        output["PHYPayload"] = bytes(PHYPayload)

        return output

    @staticmethod
    def confirmed_data_up(MacPayload:bytes, FCnt:int, FPort:int, DevAddr:bytes, NwkSKey:bytes, AppSKey:bytes, adr:bool=True, ack:bool=False) -> dict:
        
        payload = tuple(MacPayload)
        nwkSKey = tuple(NwkSKey)
        appSKey = tuple(AppSKey)

        FHDR_FCtrl_uplink_data = FHDR_FCtrl_uplink_t(adr, False, ack, False, 0)
        FHDR_FCtrl_data = FHDR_FCtrl_t((),FHDR_FCtrl_uplink_data)
        FOpts = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_MAX_FOPTS_LEN)()

        FHDR_data = FHDR_t(int(DevAddr.hex(), 16), FHDR_FCtrl_data, FCnt, FOpts)

        mac = MACPayload_t(FHDR_data, nwkSKey, appSKey, FPort, len(payload), payload)
        buffer = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX)()
        bufferSize = WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX

        length = confirmedDataUp(ctypes.byref(mac), buffer, bufferSize)

        output = {}
        PHYPayload = []
        for i in range(length):
            PHYPayload.append(buffer[i])
        output["PHYPayload"] = bytes(PHYPayload)

        return output

    @staticmethod
    def data_down(PHYPayload:bytes, DevAddr:bytes, NwkSKey:bytes, AppSKey:bytes) -> dict:
        
        phyPayload = bytes(PHYPayload)
        nwkSKey = tuple(NwkSKey)
        appSKey = tuple(AppSKey)

        FHDR_FCtrl_downlink_data = FHDR_FCtrl_downlink_t(False, False, False, False, 0)
        FHDR_FCtrl_data = FHDR_FCtrl_t(FHDR_FCtrl_downlink_data, ())
        FOpts = (ctypes.c_uint8 * WrapperLoRaMAC.LORAWAN_MAX_FOPTS_LEN)()
        
        FHDR_data = FHDR_t(int(DevAddr.hex(), 16), FHDR_FCtrl_data, 0, FOpts)

        payloadSize = WrapperLoRaMAC.LORAWAN_BUFFER_SIZE_MAX
        payload = (ctypes.c_uint8 * payloadSize)()

        mac = MACPayload_t(FHDR_data, nwkSKey, appSKey, 0, payloadSize, payload)
        
        bufferSize = len(phyPayload)
        buffer = (ctypes.c_uint8 * bufferSize)()

        ctypes.memmove(ctypes.addressof(buffer), phyPayload, bufferSize)

        status = dataDown(ctypes.byref(mac), buffer, bufferSize)
        
        if status == False:
            return None
        
        output = {}
        macPayload = []
        for i in range(mac.payloadSize):
            macPayload.append(mac.payload[i])
        output["MacPayload"]=bytes(macPayload)
        output["ADR"]=bool(mac.FHDR.FCtrl.downlink.ADR)
        output["RFU"]=bool(mac.FHDR.FCtrl.downlink.RFU)
        output["ACK"]=bool(mac.FHDR.FCtrl.downlink.ACK)
        output["FCntDown"]=int(mac.FHDR.FCnt16)
        output["FPortDown"]=int(mac.FPort)

        return output



