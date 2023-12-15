import ctypes
from enum import IntEnum

class MessageType(IntEnum):
    JOIN_REQUEST          = 0
    JOIN_ACCEPT           = 1
    UNCONFIRMED_DATA_UP   = 2
    UNCONFIRMED_DATA_DOWN = 3
    CONFIRMED_DATA_UP     = 4
    CONFIRMED_DATA_DOWN   = 5
    REJOIN_REQUEST        = 6
    PROPRIETARY           = 7

LORAWAN_MAX_FOPTS_LEN     = 15
LORAWAN_MAX_PAYLOAD_LEN   = 224

def HEX(field_value):
    value = hex(field_value)[2:].upper()
    if len(value) == 1:
        value = "0" + value
    return value

class MHDR_MType_t(ctypes.c_uint8):
    MTYPE_JOIN_REQUEST          = 0
    MTYPE_JOIN_ACCEPT           = 1
    MTYPE_UNCONFIRMED_DATA_UP   = 2
    MTYPE_UNCONFIRMED_DATA_DOWN = 3
    MTYPE_CONFIRMED_DATA_UP     = 4
    MTYPE_CONFIRMED_DATA_DOWN   = 5
    MTYPE_REJOIN_REQUEST        = 6
    MTYPE_PROPRIETARY           = 7

# Define DLsettings_t struct
class DLsettings_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("Rx2DR", ctypes.c_uint8, 4),
        ("Rx1DRoffset", ctypes.c_uint8, 3),
        ("OptNeg", ctypes.c_uint8, 1)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define CFlist_t struct
class CFlist_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("FreqCH4", ctypes.c_uint8 * 3),
        ("FreqCH5", ctypes.c_uint8 * 3),
        ("FreqCH6", ctypes.c_uint8 * 3),
        ("FreqCH7", ctypes.c_uint8 * 3),
        ("FreqCH8", ctypes.c_uint8 * 3)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            elif isinstance(field_value, (list, tuple, ctypes.Array)):
                field_value = f"[{', '.join(map(HEX, field_value))}]"
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define FHDR_FCtrl_downlink_t struct
class FHDR_FCtrl_downlink_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("ADR", ctypes.c_uint8, 1),
        ("RFU", ctypes.c_uint8, 1),
        ("ACK", ctypes.c_uint8, 1),
        ("FPending", ctypes.c_uint8, 1),
        ("FOptsLen", ctypes.c_uint8, 4)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define FHDR_FCtrl_uplink_t struct
class FHDR_FCtrl_uplink_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("ADR", ctypes.c_uint8, 1),
        ("ADRACKReq", ctypes.c_uint8, 1),
        ("ACK", ctypes.c_uint8, 1),
        ("ClassB", ctypes.c_uint8, 1),
        ("FOptsLen", ctypes.c_uint8, 4)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define FHDR_FCtrl_t union
class FHDR_FCtrl_t(ctypes.Union):
    _fields_ = [
        ("downlink", FHDR_FCtrl_downlink_t),
        ("uplink", FHDR_FCtrl_uplink_t)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define FHDR_t struct
class FHDR_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("DevAddr", ctypes.c_uint32),
        ("FCtrl", FHDR_FCtrl_t),
        ("FCnt16", ctypes.c_uint16),
        ("FOpts", ctypes.c_uint8 * LORAWAN_MAX_FOPTS_LEN)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            if field_name == "DevAddr":
                field_value = HEX(field_value).zfill(8)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define JoinRequest_t struct
class JoinRequest_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("DevEUI", ctypes.c_uint8 * 8),
        ("AppEUI", ctypes.c_uint8 * 8),
        ("AppKey", ctypes.c_uint8 * 16),
        ("DevNonce", ctypes.c_uint16)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            elif isinstance(field_value, (list, tuple, ctypes.Array)):
                field_value = f"[{', '.join(map(HEX, field_value))}]"
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

# Define JoinAccept_t struct
class JoinAccept_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("AppNonce", ctypes.c_uint32),
        ("NetID", ctypes.c_uint32),
        ("DevAddr", ctypes.c_uint32),
        ("DLsettings", DLsettings_t),
        ("RxDelay", ctypes.c_uint8),
        ("CFlist", CFlist_t),
        ("hasCFlist", ctypes.c_bool),
        ("DevNonce", ctypes.c_uint16),
        ("AppKey", ctypes.c_uint8 * 16),
        ("NwkSKey", ctypes.c_uint8 * 16),
        ("AppSKey", ctypes.c_uint8 * 16)
    ]

    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            elif isinstance(field_value, (list, tuple, ctypes.Array)):
                field_value = f"[{', '.join(map(HEX, field_value))}]"
            if field_name == "DevAddr":
                field_value = HEX(field_value).zfill(8)
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

class MACPayload_t(ctypes.LittleEndianStructure):
    _fields_ = [
        ("FHDR", FHDR_t),
        ("NwkSKey", ctypes.c_uint8 * 16),
        ("AppSKey", ctypes.c_uint8 * 16),
        ("FPort", ctypes.c_uint8),
        ("payloadSize", ctypes.c_uint8),
        ("payload", ctypes.c_uint8 * LORAWAN_MAX_PAYLOAD_LEN)
    ]
    def __str__(self) -> str:
        fields = []
        for field in self._fields_:
            field_name = field[0]
            field_value = getattr(self, field_name)
            if isinstance(field_value, ctypes.LittleEndianStructure):
                field_value = str(field_value)
            elif isinstance(field_value, (list, tuple, ctypes.Array)):
                field_value = f"[{', '.join(map(HEX, field_value))}]"
            fields.append(f"{field_name}={field_value}")

        return f"{type(self).__name__}({', '.join(fields)})"

