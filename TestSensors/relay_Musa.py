
########  https://github.com/MartinMatta/RPi_PCF8574/blob/master/main.py
import smbus
import time

class PCF8574:

    def __init__(self, addr, rev=0):
        self._bus = smbus.SMBus(rev)
        self._addr = addr
        self._pin_state = [1, 1, 1, 1,
                   1, 1, 1, 1]
        self._bus.write_byte(self._addr,0x0)

    def write(self, pin, state):
        data = 0
        self._pin_state[pin] = state

        for i, state in enumerate(self._pin_state):
            if state == 1:
                data = data +  2**i

        data = int(hex(data), 16)

        self._bus.write_byte(self._addr, data)

        return hex(data)

    def read(self, pin):
        data = self._bus.read_byte(self._addr)
        data = format(data, "0>8b")
        pin += 1
        return int(data[-pin])

#######################################################################3

relay_ON = 0
relay_OFF = 1
pcf8574 = PCF8574(0x20)


pcf8574.write(0, relay_ON) # pin0 is HIGH
pcf8574.write(1, relay_ON) # pin1 is HIGH


for i in range(0,8):  # read all pins 0-7
    print(1 - pcf8574.read(i))

time.sleep(2)

pcf8574.write(0, relay_OFF) # pin0 is LOW
pcf8574.write(1, relay_OFF) # pin3 is LOW

for i in range(0,8):  # read all pins 0-7
    print(1 - pcf8574.read(i))

#for reading individual pins:
#print(pcf8574.read(0))  # read the pin0 0:HIGH, 1:LOW
#print(pcf8574.read(1))  # read the pin1 0:HIGH, 1:LOW