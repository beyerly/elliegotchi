import utime
import machine
from eg_state import State
from eg_utils import Display, Keyboard, Voice, Nose, LightSensor, Ear

GP0 = 0 # 0, 1, 2, 3 buttons, total 3?
GP4 = 4 # SDA
GP5 = 5 # SCL
GP7 = 7 # 7, 8, 9 RGB LDE
GP10 = 10 # Sound detector (Ear)
GP16 = 16 # buzzer
GP25 = 25 # on board led
GP27 = 27 # ADC1

class Ogreenes:
    def __init__(self):
        self.state = State()
        self.dp = Display(sda=GP4, scl=GP5)
        self.kb = Keyboard(GP0, 3)
        self.voice = Voice(GP16)
        self.nose = Nose(GP7)
        self.light_sensor = LightSensor(GP27)
        self.ear = Ear(GP10)
        self.pico_led = machine.Pin(GP25, machine.Pin.OUT)
        self.diagnostics()

    def diagnostics(self):
        for counter in range(2):
            self.pico_led.value(1)
            utime.sleep(.1)
            self.pico_led.value(0)
            utime.sleep(.1)
        self.pico_led.value(1)
        self.voice.diagnostics()
        self.nose.diagnostics()
        self.ear.diagnostics()
        self.light_sensor.diagnostics()

    def live(self):
        while self.state.alive:
            # Update state
            self.state.update()

            # Update devices.
            self.dp.render(self.state)
            self.voice.vocalize(self.state)
            self.nose.update(self.state)
            self.light_sensor.update(self.state)
            self.ear.update(self.state)

            key = self.kb.read()
            if key == 0:
                # Increment current header
                _, header = self.state.get_header()
                header().input_update(5)
            elif key == 1:
                # Switch to next header
                _ = self.state.header.add(1)

            utime.sleep(self.state.timestep)
        # Final update before dying
        self.dp.eyes.update_frame(self.state)
        self.dp.render()


fred = Ogreenes()
fred.live()
