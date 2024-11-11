from eg_utils import TIMESTEP

class StateProperty:
    def __init__(self,
                 state,
                 default_value,
                 max_value,
                 wrap=False,
                 timebase = 1,
                 manual_update = True):
        self.state = state
        self.value = default_value
        self.max = max_value
        self.wrap = wrap
        # specify timebase = seconds/TIMESTEP, and with a level range of L
        # this means L*seconds s to run down an entire range.
        self.timebase = timebase
        self.manual_update = manual_update

    def input_update(self, v):
        if self.manual_update:
            self.add(v)

    def add(self, inc):
        self.value = self.value + inc
        if self.value >= self.max:
            if self.wrap:
                self.value = 0
            else:
                self.value = self.max
            return False
        elif self.value < 0:
            self.value = 0
            return False
        return True

    def set(self, v):
        self.value = v

    def scaled_value(self, scale):
        return int(scale*(self.value/self.max))

    def update_event(self, time):
        return (time % self.timebase) == 0

    def update(self):
        if self.update_event(self.state.time):
            # Natural decay
            _ = self.add(-1)

class StateAge(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1, manual_update = False):
        super().__init__(state, default_value, max_value, wrap, timebase, manual_update)

    def update(self):
        if self.update_event(self.state.time):
            # Natural aging, die if max age.
            self.state.alive = self.add(1)

class StateEnergy(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)
        self.critical_level = 10

    def input_update(self, v):
        if self.manual_update:
            self.state.happiness.add(v)
            self.add(v)

    def update(self):
        if self.update_event(self.state.time):
            # Natural decay, die if no energy.
            if self.state.asleep:
                self.state.alive = self.add(-1)
            else:
                self.state.alive = self.add(-2)

class StateHappiness(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1, manual_update = False):
        super().__init__(state, default_value, max_value, wrap, timebase, manual_update)

    def update(self):
        if self.update_event(self.state.time):
            if self.state.energy.value <= 30:
                # unhappy if low energy (hungry)
                self.add(-2)
            if self.state.fatigue.value >= 80:
                # unhappy if tired
                self.add(-3)
            if not self.state.asleep:
                # Natural decay
                _ = self.add(-1)

class StateArousal(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1, manual_update = False):
        super().__init__(state, default_value, max_value, wrap, timebase, manual_update)

    def update(self):
        if self.state.asleep:
            self.set(0)
        if self.update_event(self.state.time):
            # Natural decay
            _ = self.add(-1)

class StateAttention(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

    def input_update(self, v):
        if self.manual_update:
            self.state.arousal.add(v)
            self.add(v)

    def update(self):
        if self.state.env.sound:
            self.add(3)
            self.state.arousal.add(3)
        if self.update_event(self.state.time):
            if not self.state.asleep:
                # Natural decay
                _ = self.add(-1)

class StateFatigue(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1, manual_update = False):
        super().__init__(state, default_value, max_value, wrap, timebase, manual_update)
        self.time_dark = 0
        self.time_to_falling_asleep = 0 # number of updates

    def update(self):
        if ((not self.state.env.dark) or
            (self.state.energy.value <= self.state.energy.critical_level) or
            self.state.env.sound):
            # Wake up when light, hungry or sound.
            self.state.asleep = False
        if self.update_event(self.state.time):
            if self.state.env.dark:
                if self.time_dark >= self.time_to_falling_asleep:
                    self.state.asleep = True
                    _ = self.add(-1)
                else:
                    self.time_dark = self.time_dark + 1
            else:
                _ = self.add(1)
                self.state.asleep = False
                self.time_dark = 0

class Environment:
    def __init__(self):
        self.dark = False
        self.sound = False
        self.generating_sound = False

class State:
    def __init__(self):
        self.age = StateAge(self,0,1000, False, int(60*10/TIMESTEP))
        self.energy = StateEnergy(self,80, 100, False, int(60*6/TIMESTEP))
        self.attention = StateAttention(self, 50, 100, False, int(10/TIMESTEP))
        self.happiness = StateHappiness(self,70, 100, False, int(60/TIMESTEP))
        self.arousal = StateArousal(self,50, 100, False, int(50/TIMESTEP))
        self.fatigue = StateFatigue(self,50, 100, False, int(60*3/TIMESTEP))
        self.headers = {'age' : self.get_age,
                        'energy': self.get_energy,
                        'attention': self.get_attention,
                        'happiness': self.get_happiness,
                        'arousal': self.get_arousal,
                        'fatigue': self.get_fatigue}
        self.header = StateProperty(self,0,len(self.headers), True)
        self.alive = True
        self.asleep = False
        self.env = Environment()
        self.time = 0
        self.timestep = .1

    def update(self):
        self.age.update()
        self.energy.update()
        self.happiness.update()
        self.arousal.update()
        self.attention.update()
        self.fatigue.update()
        self.time = self.time + 1

    def get_age(self):
        return self.age
    def get_energy(self):
        return self.energy
    def get_attention(self):
        return self.attention
    def get_happiness(self):
        return self.happiness
    def get_arousal(self):
        return self.arousal
    def get_fatigue(self):
        return self.fatigue

    def get_header(self):
        hdr = sorted(list(self.headers.keys()))[self.header.value]
        return hdr, self.headers[hdr]
