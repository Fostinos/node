import ctypes, os
from sys import platform
from .loramac_types import *

__currentdir = os.path.dirname(os.path.realpath(__file__))

if platform == "win32" : 
    libLoRaMAC = ctypes.CDLL(os.path.join(__currentdir, "loramac.dll"))
elif platform == "linux":
    libLoRaMAC = ctypes.CDLL(os.path.join(__currentdir, "loramac.so"))


messageType = libLoRaMAC.LoRaWAN_MessageType
messageType.argtypes = [ctypes.POINTER(ctypes.c_uint8), 
                        ctypes.c_uint8]
messageType.restype = MHDR_MType_t


joinRequest = libLoRaMAC.LoRaWAN_JoinRequest
joinRequest.argtypes = [ctypes.POINTER(JoinRequest_t), 
                        ctypes.POINTER(ctypes.c_uint8), 
                        ctypes.c_uint8]
joinRequest.restype = ctypes.c_uint8


joinAccept = libLoRaMAC.LoRaWAN_JoinAccept
joinAccept.argtypes = [ctypes.POINTER(JoinAccept_t), 
                        ctypes.POINTER(ctypes.c_uint8), 
                        ctypes.c_uint8]
joinAccept.restype = ctypes.c_bool


unconfirmedDataUp = libLoRaMAC.LoRaWAN_UnconfirmedDataUp
unconfirmedDataUp.argtypes  =  [ctypes.POINTER(MACPayload_t), 
                                ctypes.POINTER(ctypes.c_uint8), 
                                ctypes.c_uint8]
unconfirmedDataUp.restype = ctypes.c_uint8


confirmedDataUp = libLoRaMAC.LoRaWAN_ConfirmedDataUp
confirmedDataUp.argtypes  =  [ctypes.POINTER(MACPayload_t), 
                                ctypes.POINTER(ctypes.c_uint8), 
                                ctypes.c_uint8]
confirmedDataUp.restype = ctypes.c_uint8


dataDown = libLoRaMAC.LoRaWAN_DataDown
dataDown.argtypes = [ctypes.POINTER(MACPayload_t), 
                    ctypes.POINTER(ctypes.c_uint8), 
                    ctypes.c_uint8]
dataDown.restype = ctypes.c_bool



