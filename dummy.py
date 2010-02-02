import threading
import time
import math
import random
from scope import scope_capabilities, scope_horiz, scope_vertical

class dummy_scope:
    def __init__(self, port):
        self.state = None
        self.trigger_state = "stopped"
        pass
    
    def set_state(self, state):
        self.state = state

    def reset(self):
        self.trigger_state = "stopped"

    def run(self):
        self.trigger_state = "pretrigger"
        self.thread = threading.Thread(target=self.run_thread)
        self.thread.start()

    def stop(self):
        pass

    def force_trigger(self):
        self.trigger_state = "triggered"

    def configure_all(self):
        pass
    
    def get_trigger_status(self):
        return self.trigger_state

    def wait_for_trigger(self):
        while True:
            if self.get_trigger_status() == "data ready":
                return

    def read_data(self):
        self.trigger_state = "stopped"
        x_offset = -(self.state.trigger_position/10)*self.state.time_per_div
        x_scale = self.state.time_per_div*10/1000
        r = random.randrange(100)
        y = [math.sin(2*math.pi*(x*x_scale+x_offset)/10e-3)*5.0+math.sin(2*math.pi*((x+r)*x_scale*7/10e-3)) for x in range(1000)]
        return [(x*x_scale+x_offset, y[x]) for x in range(1000)]

    def get_capabilities(self):
        return capabilities
    
    def run_thread(self):
        self.trigger_state = "pretrigger"
        while self.trigger_state != "stopped":
            time.sleep(.25)
            if self.trigger_state == "pretrigger":
                self.trigger_state = "waiting"
            elif self.trigger_state == "waiting":
                self.trigger_state = "triggered"
            elif self.trigger_state == "triggered":
                self.trigger_state = "data ready" 

vertical = scope_vertical(-20, 20, [.1, .2, .5, 1, 2, 5])
horiz = scope_horiz([500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.0])
capabilities = scope_capabilities(horiz, vertical)
