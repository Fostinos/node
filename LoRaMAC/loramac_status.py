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
    TX_NETWORK_ACK      = 1
    TX_JOIN_ERROR       = 2
    TX_PAYLOAD_ERROR    = 3


class ReceiveStatus(Enum):
    """
    Enumeration that represents different receive status codes.
    """
    RX_OK               = 0
    RX_PAYLOAD_ERROR    = 1
    RX_TIMEOUT_ERROR    = 2

    
class RadioStatus(Enum):
    """
    Enumeration that represents different LoRa radio status codes.
    """
    STATUS_DEFAULT       = 0
    STATUS_TX_WAIT       = 1
    STATUS_TX_TIMEOUT    = 2
    STATUS_TX_DONE       = 3
    STATUS_RX_WAIT       = 4
    STATUS_RX_CONTINUOUS = 5
    STATUS_RX_TIMEOUT    = 6
    STATUS_RX_DONE       = 7
    STATUS_HEADER_ERR    = 8
    STATUS_CRC_ERR       = 9
    STATUS_CAD_WAIT      = 10
    STATUS_CAD_DETECTED  = 11
    STATUS_CAD_DONE      = 12