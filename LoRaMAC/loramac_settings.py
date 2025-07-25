

################## LoRa Radio Settings
# SPI Raspberry Pi (SPI0)
RADIO_SPI_BUS_ID        = 0
RADIO_SPI_CS_ID         = 0
# RESET and BUSY pins
RADIO_RESET_PIN         = 16
RADIO_BUSY_PIN          = 6
# IRQ pin not used (set to -1). TX and RX pins not used (set to -1)
RADIO_IRQ_PIN           = -1
RADIO_TX_ENABLE_PIN     = -1
RADIO_RX_ENABLE_PIN     = -1


################# LoRaWAN Specification
UPLINK_RX1_DELAY        = 1
UPLINK_RX2_DELAY        = 2
JOIN_RX1_DELAY          = 5
JOIN_RX2_DELAY          = 6
LORA_CODING_RATE        = 5       # default coding rate : 4/5
LORA_SYNC_WORD          = 0x34    # public network
LORA_PREAMBLE_SIZE      = 8
LORA_PAYLOAD_MAX_SIZE   = 255
LORA_DEFAULT_TX_POWER   = 17      # 17 dBm
UPLINK_IQ_POLARITY      = False
DOWNLINK_IQ_POLARITY    = True
UPLINK_CRC_TYPE         = True    # enabled
DOWNLINK_CRC_TYPE       = False   # disabled

