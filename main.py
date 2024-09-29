import utime

import machine
from elliegotchi import elliegotchi

led = machine.Pin(25, machine.Pin.OUT)

for i in range(4):
    led.value(1)
    utime.sleep(0.2)
    led.value(0)
    utime.sleep(0.2)

elliegotchi = elliegotchi()
elliegotchi.live()
