from enum import Enum

class JoinStatus(Enum):
    JOIN_OK             = 0
    JOIN_MAX_TRY_ERROR  = 1
    JOIN_REQUEST_ERROR  = 2
    JOIN_ACCEPT_ERROR   = 3
    


class TransmitStatus(Enum):
    TX_OK               = 0
    TX_JOIN_ERROR       = 1
    TX_PAYLOAD_ERROR    = 2


class ReceiveStatus(Enum):
    RX_OK               = 0
    RX_PAYLOAD_ERROR    = 1