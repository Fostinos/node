from enum import Enum


class EU868():
    """
    This class defines the parameters specific to the EU868 region for LoRaWAN communication.
    """
    UPLINK_FREQUENCY_CHANNEL_0   = 868100000       # 868.1 Mhz
    UPLINK_FREQUENCY_STEP        = 200000          # 0.2 Mhz
    DOWNLINK_FREQUENCY_CHANNEL_0 = 868100000       # 868.1 Mhz
    DOWNLINK_FREQUENCY_STEP      = 200000          # 0.2 Mhz
    RX2_FREQUENCY                = 869525000       # 869.525 Mhz
    UPLINK_BANDWIDTH             = 125000          # 125 khz
    DOWNLINK_BANDWIDTH           = 125000          # 125 khz
    SPREADING_FACTOR_MIN         = 7
    SPREADING_FACTOR_MAX         = 12
    UPLINK_CHANNEL_MIN           = 0
    UPLINK_CHANNEL_MAX           = 7
    JOIN_CHANNEL_MAX             = 3


class US915():
    """
    This class defines the parameters specific to the US915 region for LoRaWAN communication.
    """
    UPLINK_FREQUENCY_CHANNEL_0   = 902300000       # 902.3 Mhz
    UPLINK_FREQUENCY_STEP        = 200000          # 0.2 Mhz
    DOWNLINK_FREQUENCY_CHANNEL_0 = 923300000       # 923.3 Mhz
    DOWNLINK_FREQUENCY_STEP      = 600000          # 0.6 Mhz
    RX2_FREQUENCY                = 923300000       # 923.3 Mhz
    UPLINK_BANDWIDTH             = 125000          # 125 khz
    DOWNLINK_BANDWIDTH           = 500000          # 500 khz
    SPREADING_FACTOR_MIN         = 7
    SPREADING_FACTOR_MAX         = 10
    UPLINK_CHANNEL_MIN           = 0
    UPLINK_CHANNEL_MAX           = 63


class Region(Enum):
    """
    Represents different regions and provides a method to calculate the uplink frequency based on the region and channel.
    """
    EU868 = EU868()
    US915 = US915()

    def uplink_frequency(self, channel:int) -> int:
        """
        Calculates the uplink frequency based on the region and channel.

        Args:
            channel (int): The channel number.

        Returns:
            int: The calculated uplink frequency.
        """
        if self == Region.EU868 and channel > 2:
            return self.value.UPLINK_FREQUENCY_CHANNEL_0 - (8 - channel) * self.value.UPLINK_FREQUENCY_STEP
        return self.value.UPLINK_FREQUENCY_CHANNEL_0 + channel * self.value.UPLINK_FREQUENCY_STEP

    def downlink_frequency(self, channel:int) -> int:
        """
        Calculates the downlink frequency based on the region and channel.

        Args:
            channel (int): The channel number.

        Returns:
            int: The calculated downlink frequency.
        """
        if self == Region.EU868 and channel > 2:
            return self.value.UPLINK_FREQUENCY_CHANNEL_0 - (8 - channel) * self.value.UPLINK_FREQUENCY_STEP
        return self.value.DOWNLINK_FREQUENCY_CHANNEL_0 + (channel % 8) * self.value.DOWNLINK_FREQUENCY_STEP
