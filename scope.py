# Stores the current state of the GUI settings for passing to the backend
class scope_state:
    def __init__(self):
        self.time_per_div = 500e-9
        self.volts_per_div = 0.1
        self.vertical_offset = 0.0
        self.trigger_voltage = 1.0
        self.trigger = "rising"
        self.trigger_position = 25.0

    def copy(self):
        s = scope_state()
        s.time_per_div = self.time_per_div
        s.volts_per_div = self.volts_per_div
        s.vertical_offset = self.vertical_offset
        s.trigger_voltage = self.trigger_voltage
        s.trigger = self.trigger
        s.trigger_position = self.trigger_position
        return s

# Passes the capabilities of the backend to the GUI
class scope_capabilities:
    def __init__(self, horiz, vertical):
        self.horiz = horiz
        self.vertical = vertical

class scope_horiz:
    class entry:
        def __init__(self, time_per_div, custom):
            self.time_per_div = time_per_div
            self.custom = custom
        def get_time_per_div(self): return self.time_per_div
        def get_custom(self, val): return self.custom[val]

    def __init__(self, valid_horiz=[]):
        self.vals = valid_horiz
    def add_valid_horiz(self, horiz): self.valid_horiz.append(horiz)
    def get_valid_horiz(self): return self.valid_horiz
    def get(self, i):
        return self.valid_horiz[i]

class scope_vertical:
    def __init__(self, min, max, vals):
        self.min = min
        self.max = max
        self.vals = vals
