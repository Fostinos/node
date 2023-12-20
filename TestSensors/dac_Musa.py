import smbus
import time

# I2C adresi (MCP4725 için genellikle 0x60)
MCP4725_ADDR = 0x4C

# I2C kanalını başlat
bus = smbus.SMBus(1)  # 0 numaralı I2C kanalı kullanılıyor, Raspberry Pi'nin modeline göre değişebilir


def set_voltage(voltage):
    # Voltajı 0 ile 3.3 Volt arasında sınırlama
    voltage = max(0, min(3.3, voltage))

    # Voltajı 12-bit olarak MCP4725'e yazma
    dac_value = int((voltage / 3.3) * 4095)

    # MCP4725'e yazma işlemi
    data = [(dac_value >> 4) & 0xFF, (dac_value << 4) & 0xFF]
    bus.write_i2c_block_data(MCP4725_ADDR, 0x40, data)


# Ana döngü
while True:
    try:
        # Kullanıcıdan voltaj girişi alınması
        voltage_input = float(input("Enter a voltage (0 - 3.3 Volt) :"))

        # Girilen voltajı ayarlamak
        set_voltage(voltage_input)

        print("Set Voltage is: {} Volt".format(voltage_input))

    except ValueError:
        print("Invalid voltage. Please enter a valid value!")

    time.sleep(1)
