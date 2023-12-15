

class Device():
    """
    The `Device` class represents a device in a LoRaWAN network.
    It has attributes to store information such as device identifiers, encryption keys,
    payload data, and network settings. The class provides methods to convert the device 
    object to a dictionary and to set the device attributes from a dictionary.
    """

    def __init__(self, DevEUI:str, AppEUI:str, AppKey:str):
        """
        Initializes a new `Device` object with the provided device identifiers and encryption keys.

        Args:
            DevEUI (str): The device's EUI (Extended Unique Identifier).
            AppEUI (str): The application's EUI.
            AppKey (str): The application's encryption key.

        Raises:
            ValueError: If the length of DevEUI is not 16, AppEUI is not 16, or AppKey is not 32.
        """
        if len(DevEUI) != 16:
            raise ValueError("Device : DevEUI invalid")
        if len(AppEUI) != 16:
            raise ValueError("Device : AppEUI invalid")
        if len(AppKey) != 32:
            raise ValueError("Device : AppKey invalid")
        self.DevEUI = bytes.fromhex(DevEUI)
        self.AppEUI = bytes.fromhex(AppEUI)
        self.AppKey = bytes.fromhex(AppKey)
        self.DevAddr = bytes([])
        self.NwkSKey = bytes([])
        self.AppSKey = bytes([])
        self.FCnt = 0
        self.FPort = 2
        self.DevNonce = 0
        self.isJoined = False
        self.channelGroup = 0
        
        # LoRaWAN payloads
        self.uplinkMacPayload = bytes([])     # unencrypted uplink payload
        self.downlinkMacPayload = bytes([])   # unencrypted uplink payload
        self.uplinkPhyPayload = bytes([])     # encrypted uplink payload
        self.downlinkPhyPayload = bytes([])   # encrypted uplink payload
        # other LoRaMAC info
        self.Adr = True
        self.Ack = True
        self.Rfu = False
        self.FCntDown = 0
        self.FPortDown = 0
        self.AckDown = False
        self.join_max_tries = 0
        self.uplink_channel_min = 0
        self.uplink_channel_max = self.uplink_channel_min + 7 * (self.channelGroup + 1)
        self.rx2_window_time : float = -1
        self.rx2_window_timeout : float = -1
        self.message_type = None
        self.confirmed_uplink = False


    def to_dict(self) -> dict:
        """
        Converts the device object to a dictionary.

        Returns:
            dict: A dictionary containing the attributes of the Device instance.
        """
        device_dict = {
            "DevEUI": self.DevEUI.hex(),
            "AppEUI": self.AppEUI.hex(),
            "AppKey": self.AppKey.hex(),
            "DevAddr": self.DevAddr.hex(),
            "NwkSKey": self.NwkSKey.hex(),
            "AppSKey": self.AppSKey.hex(),
            "FCnt": self.FCnt,
            "FPort": self.FPort,
            "DevNonce": self.DevNonce,
            "isJoined": self.isJoined,
            "channelGroup": self.channelGroup,
        }
        return device_dict

    def set_device(self, device_dict:dict):
        """
        Sets the device attributes from a dictionary.

        Args:
            device_dict (dict): A dictionary containing the device attributes.
        """
        try:
            for key, value in device_dict.items():
                if hasattr(self, key):
                    if key == "isJoined":
                        setattr(self, key, bool(value))
                    elif isinstance(value, int):
                        setattr(self, key, value)
                    elif isinstance(value, str):
                        setattr(self, key, bytes.fromhex(value))
        except:
            pass