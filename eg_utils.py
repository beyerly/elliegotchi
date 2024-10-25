import framebuf
import math
import utime
import random
import machine
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

TIMESTEP = 0.1

class Frame:
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.pos = [0, 0] # [x, y]
        self.fb = framebuf.FrameBuffer(bytearray(int(height*width/8)), width, height, framebuf.MONO_HLSB)

    def random_event(self, chance):
        return random.random() < chance

    def clear(self):
        self.fb.fill(0)


class Eyes(Frame):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.pos = [50, 30]  # [x, y]
        self.eye_radius_x = 20
        self.eye_radius_y = 20
        self.eyebrow_angle = 0 # 0 is flat, 10 is sad angle, -10 is angry angle
        self.dead_eye_size = 10
        self.eye_distance = 40
        self.pupil_radius = 5
        self.gaze_direction = 1  # -1 is straight ahead, angle in deg otherwise
        self.blink_count = 0
        self.blink_rate = 0.03  # % chance of blink
        self.gaze_rate = 0.05  # % chance of blink
        self.blink_duration = 1  # render intervals
        self.render_eyes(1)
        self.render_eyebrows(1)
        self.render_pupils(1)
        self.eyes_state = "open"

    def render_eyes(self, draw):
        # left eye
        self.fb.ellipse(self.pos[0],
                        self.pos[1],
                        self.eye_radius_x,
                        self.eye_radius_y,
                        draw)
        # right eye
        self.fb.ellipse(self.pos[0] + self.eye_distance,
                        self.pos[1],
                        self.eye_radius_x,
                        self.eye_radius_y,
                        draw)

    def render_eyebrows(self, draw):
        self.fb.line(self.pos[0] - self.eye_radius_x,
                     self.pos[1] - self.eye_radius_y + self.eyebrow_angle,
                     self.pos[0] + self.eye_radius_x,
                     self.pos[1] - self.eye_radius_y - self.eyebrow_angle,
                     draw)
        self.fb.line(self.pos[0] + self.eye_distance - self.eye_radius_x,
                     self.pos[1] - self.eye_radius_y - self.eyebrow_angle,
                     self.pos[0] + self.eye_distance + self.eye_radius_x,
                     self.pos[1] - self.eye_radius_y + self.eyebrow_angle,
                     draw) 

    def render_sleep(self, draw):
        self.fb.line(self.pos[0] - self.eye_radius_x,
                     self.pos[1],
                     self.pos[0] + self.eye_radius_x,
                     self.pos[1],
                     draw)
        self.fb.line(self.pos[0] + self.eye_distance - self.eye_radius_x,
                     self.pos[1],
                     self.pos[0] + self.eye_distance + self.eye_radius_x,
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
        self.fb.ellipse(self.pos[0] + int(math.sin(self.gaze_direction) * self.eye_radius_x / 2),
                        self.pos[1] + int(math.cos(self.gaze_direction) * self.eye_radius_y / 2),
                        self.pupil_radius,
                        self.pupil_radius,
                        draw,
                        True)
        # right pupil
        self.fb.ellipse(self.pos[0] + self.eye_distance
                        + int(math.sin(self.gaze_direction) * self.eye_radius_x / 2),
                        self.pos[1] + int(math.cos(self.gaze_direction) * self.eye_radius_y / 2),
                        self.pupil_radius,
                        self.pupil_radius,
                        draw,
                        True)

    def blink(self):
        self.eyes_state = 'blink'
        self.blink_count = 0

    def update_frame(self, state):
        self.clear()
        if not state.alive:
            self.eyes_state = 'dead'
        # Eyes more open with mor arousal
        self.eye_radius_y = 10 + int(10*(state.arousal.value/state.arousal.max))
        # If in sad/angry quadrant, set eyebrow angle
        if (state.happiness.value / state.happiness.max) < .5:
            self.eyebrow_angle = -1*int(20*(state.arousal.value/state.arousal.max)) + 10
        else:
            self.eyebrow_angle = 1

        if self.eyes_state == 'open':
            self.render_eyes(1)
            self.render_eyebrows(1)
            self.render_pupils(1)
        elif self.eyes_state == 'blink':
            self.render_sleep(1)
        elif self.eyes_state == 'sleep':
            self.render_sleep(1)
        elif self.eyes_state == 'dead':
            self.render_dead(1)

    def autonomous_events(self):
        update = False
        if self.eyes_state == 'blink':
            self.blink_count = self.blink_count + 1
            if self.blink_count > self.blink_duration:
                self.eyes_state = 'open'
                update = True
        elif self.eyes_state == 'open':
            if self.random_event(self.blink_rate):
                self.blink()
                update = True
            if self.random_event(self.gaze_rate):
                self.gaze_direction = random.random() * 6
                update = True
        #if update:
        #    self.update_frame()


class Header(Frame):
    def __init__(self, width, height):
        super().__init__(width,height)
        self.text = 'Ogreenes'
        self.value = 0
        self.render_text(1)

    def render_text(self, draw):
        self.fb.text(self.text + ": " + str(self.value),
                     self.pos[0],
                     self.pos[1],
                     draw)

    def update_frame(self, state):
        self.clear()
        self.text, value_getter = state.get_header()
        self.value = value_getter().value
        self.render_text(1)


class Levels(Frame):
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
        _, value_getter = state.get_header()
        self.level = value_getter().scaled_value(self.height)
        self.render_levels(1)

class Display:
    def __init__(self, sda, scl):
        self.width = 128  # oled display width
        self.height = 64  # oled display height
        self.sda = machine.Pin(sda)
        self.scl = machine.Pin(scl)
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
        self.header = Header(self.header_size[0], self.header_size[1])
        self.levels = Levels(self.levels_size[0], self.levels_size[1])
        self.eyes = Eyes(self.eyes_size[0], self.eyes_size[1])

    def update(self, state):
        self.eyes.autonomous_events()
        self.eyes.update_frame(state)
        self.header.update_frame(state)
        self.levels.update_frame(state)

    def render(self, state):
        self.update(state)
        self.oled.blit(self.header.fb, self.header_pos[0][0], self.header_pos[0][1])
        self.oled.blit(self.eyes.fb, self.eyes_pos[0][0], self.eyes_pos[0][1])
        self.oled.blit(self.levels.fb, self.levels_pos[0][0], self.levels_pos[0][1])
        self.oled.show()

class Keyboard:
    def __init__(self, gp, buttons):
        self.buttons = buttons
        self.button = []
        self.lastbutton = None
        for i in range(gp, gp + self.buttons):
            self.button.append(machine.Pin(i, machine.Pin.IN))

    def read(self):
        button = None
        for i in range(self.buttons):
            if self.button[i].value() == 1:
                if self.lastbutton != i:
                    button = i
                    continue
        if button is None:
            self.lastbutton = None
        if self.lastbutton != button:
            self.lastbutton = button
            return button
        else:
            return None

class Mood:
    def __init__(self, repeat_range, pitch_range, pitch_step, step_speed, repeat_delay, duty_cycle, occurrence):
        self.repeat_range = repeat_range
        self.pitch_range = pitch_range
        self.pitch_step = pitch_step
        self.step_speed = step_speed
        self.repeat_delay = repeat_delay
        self.duty_cycle = duty_cycle
        self.occurrence = occurrence  # every n seconds

class Voice:
    def __init__(self, gp):
        self.buzzer = machine.PWM(machine.Pin(gp))
        angry = Mood(repeat_range=[3, 5],
                        pitch_range=[1500, 3000],
                        pitch_step=-1,
                        step_speed=0,
                        repeat_delay=0.2,
                        duty_cycle=30000,
                        occurrence=int(10/TIMESTEP))
        joy = Mood(repeat_range=[4, 7],
                     pitch_range=[1500, 3000],
                     pitch_step=1,
                     step_speed=0.0001,
                     repeat_delay=0.2,
                     duty_cycle=20000,
                     occurrence=int(60*2/TIMESTEP))
        content = Mood(repeat_range=[1, 3],
                     pitch_range=[300, 1000],
                     pitch_step=-1,
                     step_speed=0.001,
                     repeat_delay=0.5,
                     duty_cycle=5000,
                     occurrence=int(60*5/TIMESTEP))
        depressed = Mood(repeat_range=[4, 7],
                     pitch_range=[300, 800],
                     pitch_step=-1,
                     step_speed=0.001,
                     repeat_delay=0.2,
                     duty_cycle=10000,
                     occurrence=int(60/TIMESTEP))
        self.moods = {'angry': angry,
                      'joy': joy,
                      'content': content,
                      'depressed': depressed}
        self.mood = 'content'

    def diagnostics(self):
        self.buzzer.freq(3000)
        self.buzzer.duty_u16(10000)
        utime.sleep(.1)
        self.buzzer.duty_u16(0)

    def randomize_range(self, r, step):
        if step>0:
            return range(r[0], r[0] + int(random.random() * (r[1] - r[0])), step)
        else:
            return range(r[1], r[0] + int(random.random() * (r[1] - r[0])), step)

    def randomize_number(self, r):
        return range(0, r[0] + int(random.random() * (r[1] - r[0])))


    def buzzer_off(self, on=True):
            self.buzzer.duty_u16(0)

    def buzzer_on(self):
            self.buzzer.duty_u16(self.moods[self.mood].duty_cycle)

    def update(self, state):
        if state.happiness.value > 50:
            if state.arousal.value > 50:
                self.mood = 'joy'
            else:
                self.mood = 'content'
        else:
            if state.arousal.value > 50:
                self.mood = 'angry'
            else:
                self.mood = 'depressed'

    def vocalize(self, state):
        print(self.mood)
        self.update(state)
        if (state.time % self.moods[self.mood].occurrence) == 0:
            for t in self.randomize_number(self.moods[self.mood].repeat_range):
                self.buzzer_on()
                for frequency in self.randomize_range(self.moods[self.mood].pitch_range, self.moods[self.mood].pitch_step):
                    self.buzzer.freq(frequency)
                    utime.sleep(self.moods[self.mood].step_speed)
                self.buzzer_off()
                utime.sleep(self.moods[self.mood].repeat_delay)


class RgbColor:
    def __init__(self, pin):
        self.max_duty = 66000
        self.min_duty = 50000
        self.range = self.max_duty - self.min_duty
        self.freq = 1000
        self.max_value = 255
        self.pin = machine.PWM(machine.Pin(pin))
        self.on()

    def on(self):
        self.pin.freq(self.freq)

    def set_value(self, value):
        self.pin.duty_u16(self.max_duty - int(self.range*value/self.max_value))


class ColorMap:
    def __init__(self):
        self.max_rgb = 255
        red = 1.7 * math.pi
        self.rgb = [red]
        for i in range(2):
            rad = self.rgb[-1] + 2 * math.pi/3
            if rad > 2 * math.pi:
                rad -= 2 * math.pi
            self.rgb.append(rad)

    def get_color(self, rad):
        rgb_out = []
        for i in self.rgb:
            # Normalize: 0 rad is the center for color
            rad_norm = rad - i
            if rad_norm < 0:
                rad_norm += 2 * math.pi
            # Split circle in 2 halves
            if rad_norm > math.pi:
                rad_norm = -1 * rad_norm + 2 * math.pi
            # Invert
            rad_norm = math.pi - rad_norm
            rgb_out.append(int(self.max_rgb * rad_norm/math.pi))
        return rgb_out

class Nose:
    def __init__(self, gp):
        self.rgb_led = []
        for i in range(3):
            self.rgb_led.append(RgbColor(gp + i))
        self.color_map = ColorMap()

    def diagnostics(self):
        self.rgb_to_color([0,0,0])
        for deg in range(360):
            rad = 2 * math.pi * deg/360
            rgb = self.color_map.get_color(rad)
            print(rgb)
            self.rgb_to_color(rgb)
            utime.sleep(0.01)

    def rgb_to_color(self, rgb):
        for i in range(3):
            self.rgb_led[i].set_value(rgb[i])

    def cartesian_to_angle(self, x, y):
        angle = math.atan2(x, y)
        if angle < 0:
            angle += 2 * math.pi
        return angle

    def cartesian_to_color(self, x, y):
        angle = self.cartesian_to_angle(x, y)
        rgb = self.color_map.get_color(angle)
        self.rgb_to_color(rgb)

    def update(self, state):
        # map to pos/neg coordinates: normalize to max/2
        x = state.happiness.value - int(state.happiness.max/2)
        y = state.arousal.value - int(state.arousal.max/2)
        self.cartesian_to_color(x, y)


