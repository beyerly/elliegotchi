import utime
from eg_utils import display

class state:
    def __init__(self):
        self.alive = True

class elliegotchi:
    def __init__(self):
        print('elliegotchi v0.1')
        self.state = state()
        self.timestep = 0.05

    def live(self):
        while self.state.alive:
            utime.sleep(self.timestep)

