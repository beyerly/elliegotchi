import framebuf
import math
import utime
import random
import machine
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C


class frame:
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.pos = [0, 0] # [x, y]
        self.fb = framebuf.FrameBuffer(bytearray(int(height*width/8)), width, height, framebuf.MONO_HLSB)

    def random_event(self, chance):
        return random.random() < chance

    def clear(self):
        self.fb.fill(0)


class eyes(frame):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.pos = [50, 30]  # [x, y]
        self.eye_radius = 20
        self.dead_eye_size = 10
        self.eye_distance = 40
        self.pupil_radius = 5
        self.gaze_direction = 1  # -1 is straight ahead, angle in deg otherwise
        self.blink_count = 0
        self.blink_rate = 0.03  # % chance of blink
        self.gaze_rate = 0.05  # % chance of blink
        self.blink_duration = 1  # render intervals
        self.render_eyes(1)
        self.render_pupils(1)
        self.state = "open"

    def render_eyes(self, draw):
        # left eye
        self.fb.ellipse(self.pos[0],
                        self.pos[1],
                        self.eye_radius,
                        self.eye_radius,
                        draw)
        # right eye
        self.fb.ellipse(self.pos[0] + self.eye_distance,
                        self.pos[1],
                        self.eye_radius,
                        self.eye_radius,
                        draw)

    def render_sleep(self, draw):
        self.fb.line(self.pos[0] - self.eye_radius,
                     self.pos[1],
                     self.pos[0] + self.eye_radius,
                     self.pos[1],
                     draw)
        self.fb.line(self.pos[0] + self.eye_distance - self.eye_radius,
                     self.pos[1],
                     self.pos[0] + self.eye_distance + self.eye_radius,
                     self.pos[1],
                     draw)

    def render_dead(self, draw):
        self.fb.line(self.pos[0] - self.dead_eye_size,
                     self.pos[1] - self.dead_eye_size,
                     self.pos[0] + self.dead_eye_size,
                     self.pos[1] + self.dead_eye_size,
                     draw)
        self.fb.line(self.pos[0] + self.dead_eye_size,
                     self.pos[1] - self.dead_eye_size,
                     self.pos[0] - self.dead_eye_size,
                     self.pos[1] + self.dead_eye_size,
                     draw)
        self.fb.line(self.pos[0] + self.eye_distance - self.dead_eye_size,
                     self.pos[1] - self.dead_eye_size,
                     self.pos[0] + self.eye_distance + self.dead_eye_size,
                     self.pos[1] + self.dead_eye_size,
                     draw)
        self.fb.line(self.pos[0] + self.eye_distance + self.dead_eye_size,
                     self.pos[1] - self.dead_eye_size,
                     self.pos[0] + self.eye_distance - self.dead_eye_size,
                     self.pos[1] + self.dead_eye_size,
                     draw)

    def render_pupils(self, draw):
        self.fb.ellipse(self.pos[0] + int(math.sin(self.gaze_direction) * self.eye_radius / 2),
                        self.pos[1] + int(math.cos(self.gaze_direction) * self.eye_radius / 2),
                        self.pupil_radius,
                        self.pupil_radius,
                        draw,
                        True)
        # right pupil
        self.fb.ellipse(self.pos[0] + self.eye_distance
                        + int(math.sin(self.gaze_direction) * self.eye_radius / 2),
                        self.pos[1] + int(math.cos(self.gaze_direction) * self.eye_radius / 2),
                        self.pupil_radius,
                        self.pupil_radius,
                        draw,
                        True)

    def blink(self):
        self.state = 'blink'
        self.blink_count = 0

    def update_frame(self, s=None):
        self.clear()
        if s:
            if not s.alive:
                self.state = 'dead'

        if self.state == 'open':
            self.render_eyes(1)
            self.render_pupils(1)
        elif self.state == 'blink':
            self.render_sleep(1)
        elif self.state == 'sleep':
            self.render_sleep(1)
        elif self.state == 'dead':
            self.render_dead(1)

    def autonomous_events(self):
        update = False
        if self.state == 'blink':
            self.blink_count = self.blink_count + 1
            if self.blink_count > self.blink_duration:
                self.state = 'open'
                update = True
        elif self.state == 'open':
            if self.random_event(self.blink_rate):
                self.blink()
                update = True
            if self.random_event(self.gaze_rate):
                self.gaze_direction = random.random() * 6
                update = True
        if update:
            self.update_frame()


class header(frame):
    def __init__(self, width, height):
        super().__init__(width,height)
        self.text = 'elliegochi'
        self.value = 0
        self.render_text(1)

    def render_text(self, draw):
        self.fb.text(self.text + ": " + str(self.value),
                     self.pos[0],
                     self.pos[1],
                     draw)

    def update_frame(self, state):
        self.clear()
        if state.header == 'age':
            self.value = state.age
        self.text = state.header
        self.render_text(1)


class levels(frame):
    def __init__(self, width, height):
        super().__init__(width,height)
        self.level = 40
        self.render_levels(1)

    def render_levels(self, draw):
        self.fb.line(self.pos[0],
                     self.pos[1] + self.height,
                     self.pos[0],
                     self.pos[1] + self.height - self.level ,
                     draw)

    def update_frame(self, state):
        self.clear()
        if state.header == 'age':
            self.level = state.age
        self.render_levels(1)

class display:
    def __init__(self):
        self.width = 128  # oled display width
        self.height = 64  # oled display height
        self.sda = machine.Pin(4)
        self.scl = machine.Pin(5)
        self.i2c = machine.I2C(0, sda=self.sda, scl=self.scl, freq=400000)
        self.oled = SSD1306_I2C(self.width, self.height, self.i2c)
        self.header_pos = [[0, 0],[self.width,8]]
        self.levels_pos = [[0, 8],[8,self.height]]
        self.eyes_pos = [[8, 8],[self.width,self.height]]
        self.header_size = [self.header_pos[1][0] - self.header_pos[0][0],
                            self.header_pos[1][1] - self.header_pos[0][1]]
        self.levels_size = [self.levels_pos[1][0] - self.levels_pos[0][0],
                            self.levels_pos[1][1] - self.levels_pos[0][1]]
        self.eyes_size = [self.eyes_pos[1][0] - self.eyes_pos[0][0],
                            self.eyes_pos[1][1] - self.eyes_pos[0][1]]
        self.header = header(self.header_size[0], self.header_size[1])
        self.levels = levels(self.levels_size[0], self.levels_size[1])
        self.eyes = eyes(self.eyes_size[0], self.eyes_size[1])

    def render(self):
        self.oled.blit(self.header.fb, self.header_pos[0][0], self.header_pos[0][1])
        self.oled.blit(self.eyes.fb, self.eyes_pos[0][0], self.eyes_pos[0][1])
        self.oled.blit(self.levels.fb, self.levels_pos[0][0], self.levels_pos[0][1])
        self.oled.show()
