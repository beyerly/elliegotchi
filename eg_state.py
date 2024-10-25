from eg_utils import TIMESTEP

class StateProperty:
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        self.state = state
        self.value = default_value
        self.max = max_value
        self.wrap = wrap
        self.timebase = timebase

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

    def scaled_value(self, scale):
        return int(scale*(self.value/self.max))

    def update_event(self, time):
        return (time % self.timebase) == 0

    def update(self):
        if self.update_event(self.state.time):
            # Natural decay
            _ = self.add(-1)

class StateAge(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

    def update(self):
        if self.update_event(self.state.time):
            # Natural aging, die if max age.
            self.state.alive = self.add(1)

class StateEnergy(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

    def update(self):
        if self.update_event(self.state.time):
            # Natural decay, die if no energy.
            self.state.alive = self.add(-1)

class StateHappiness(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

    def update(self):
        if self.update_event(self.state.time):
            if self.state.energy.value <= 50:
                self.add(-2)
            if self.state.attention.value >=50:
                self.add(2)
            # Natural decay
            _ = self.add(-1)

class StateArousal(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

class StateAttention(StateProperty):
    def __init__(self, state, default_value, max_value, wrap=False, timebase = 1):
        super().__init__(state, default_value, max_value, wrap, timebase)

class State:
    def __init__(self):
        self.age = StateAge(self,0,1000, False, int(60*10/TIMESTEP))
        self.energy = StateEnergy(self,100, 100, False, int(60*3/TIMESTEP))
        self.attention = StateAttention(self, 50, 100, False, int(45/TIMESTEP))
        self.happiness = StateHappiness(self,70, 100, False, int(60/TIMESTEP))
        self.arousal = StateArousal(self,50, 100, False, int(60*2/TIMESTEP))
        self.headers = {'age' : self.get_age,
                        'energy': self.get_energy,
                        'attention': self.get_attention,
                        'happiness': self.get_happiness,
                        'arousal': self.get_arousal}
        self.header = StateProperty(self,0,len(self.headers), True)
        self.alive = True
        self.time = 0
        self.timestep = .1

    def update(self):
        self.age.update()
        self.energy.update()
        self.happiness.update()
        self.arousal.update()
        self.attention.update()
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

    def get_header(self):
        hdr = sorted(list(self.headers.keys()))[self.header.value]
        return hdr, self.headers[hdr]
