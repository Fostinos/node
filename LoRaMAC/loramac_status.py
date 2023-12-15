from enum import Enum

class JoinStatus(Enum):
    """
    Enumeration that represents different join status codes.
    """
    JOIN_OK = 0
    JOIN_MAX_TRY_ERROR = 1
    JOIN_REQUEST_ERROR = 2
    JOIN_ACCEPT_ERROR = 3
    


class TransmitStatus(Enum):
    """
    Enumeration that represents different transmit status codes.
    """
    TX_OK               = 0
    TX_JOIN_ERROR       = 1
    TX_PAYLOAD_ERROR    = 2


class ReceiveStatus(Enum):
    """
    Enumeration that represents different receive status codes.
    """
    RX_OK               = 0
    RX_PAYLOAD_ERROR    = 1
    RX_TIMEOUT_ERROR    = 2