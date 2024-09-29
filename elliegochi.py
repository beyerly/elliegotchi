import math
import utime
import random
from eg_utils import header, levels, eyes, display

# test

class state:
    def __init__(self):
        self.health = 40
        self.age = 0
        self.maxage = 10
        self.alive = True
        self.header = 'age'

class elliegochi:
    def __init__(self):
        self.dp = display()
        self.state = state()
        self.counter = 0
        self.agecount = 100

    def update_age(self):
        header_update = False
        eyes_update = False
        if self.counter == self.agecount:
            self.state.age = self.state.age + 1
            if self.state.age == self.state.maxage:
                self.state.age = self.state.maxage
                self.state.alive = False
                eyes_update = True
            header_update = True
            self.counter = 0
        else:
            self.counter = self.counter + 1
        return header_update, eyes_update

    def live(self):
        self.dp.eyes.blink_duration = 5
        self.dp.eyes.eye_radius = 15
        while True:
            utime.sleep(0.05)
            header_update, eyes_update = self.update_age()
            if header_update:
                self.dp.header.update_frame(self.state)
                self.dp.levels.update_frame(self.state)
            if eyes_update:
                self.dp.eyes.update_frame(self.state)
            self.dp.eyes.autonomous_events()
            self.dp.render()

elliegochi = elliegochi()

elliegochi.live()


    
                         