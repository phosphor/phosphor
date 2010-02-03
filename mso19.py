import time
import sys
from scope import scope_capabilities, scope_horiz, scope_vertical

verbose = 0
def print_debug(level, s):
    if level <= verbose:
        print >>sys.stderr, s

def parse_in(s):
    ret = []
    i = 0
    while True:
        if len(s) < 3:
            break
        a=ord(s[0])-0x40
        b=ord(s[1])-0x40
        c=ord(s[2])-0x40
        ret.append((i, (512-(a | b<<6))*42.831/1000, c))
        s = s[3:]
        i += 1
    return ret

def to_base64(data):
    if data >= 0x40:
        raise Exception()
    if data >= 0x20:
        return chr(data)
    else:
        return chr(0x40+data)

def to_cmd_pair(cmd, data):
    return "%c%c" % (to_base64(cmd | (data&0xc0)>>2), to_base64(data&0x3f))

def to_cmd(s):
    return "@LDS~%s~" % s

def read_write(ser, s, delay):
    print_debug(1, "-> %s" % s)
    ser.write(s)
    time.sleep(delay/1e3)
    s = ser.read(ser.inWaiting(64))
    print_debug(1, "<- %s" % s)
    return s

def write_serial(ser, s):
    print_debug(1, "-> %s" % s)
    ser.write(s)

def read_serial(ser, len, timeout=1000):
    s=""
    start = time.time()
    while len > 0:
        if time.time() - start > timeout/1000.0:
            break
        l = ser.inWaiting(len)
        if l > len:
            l = len
        s += ser.read(l)
        len -= l
    if len > 0:
        print_debug(0, "WARNING! timeout %d bytes not read" % len)
#    if ser.inWaiting(0) > 0:
#        print_debug(0, "WARNING! QUEUED DATA: %d" % ser.inWaiting(0))
    print_debug(1, "<- %s" % s)
    return s

mso_horiz_reg = {
    500e-9: (0x02, 0x05),
    1e-6:   (0x01, 0x05),
    2e-6:   (0x00, 0x05),
    5e-6:   (0x03, 0x03),
    10e-6:  (0x03, 0x08),
    20e-6:  (0x03, 0x12),
    50e-6:  (0x03, 0x30),
    100e-6: (0x03, 0x62),
    200e-6: (0x03, 0xC6),
    500e-6: (0x07, 0xF2),
    1e-3:   (0x0F, 0xE6),
    2e-3:   (0x1F, 0xCD),
    5e-3:   (0x4f, 0x86),
    10e-3:  (0x9f, 0x0e),
    20e-3:  (0x03, 0xc7),
    50e-3:  (0x07, 0xf3),
    100e-3: (0x0f, 0xe7),
    200e-3: (0x1f, 0xcf),
    500e-3: (0x4f, 0x87),
    1.0:    (0x9f, 0x0f),
}

mso_horiz_offset = {
    500e-9: 6,
    1e-6:   6,
    2e-6:   8,
    5e-6:   1,
    10e-6:  1,
    20e-6:  1,
    50e-6:  1,
    100e-6: 1,
    200e-6: 1,
    500e-6: 1,
    1e-3:   1,
    2e-3:   1,
    5e-3:   1,
    10e-3:  1,
    20e-3:  1,
    50e-3:  1,
    100e-3: 1,
    200e-3: 1,
    500e-3: 1,
    1.0:    1,
}

mso_vertical = scope_vertical(-20, 20, [.1, .2, .5, 1, 2, 5])
mso_horiz = scope_horiz([500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.0])
mso_capabilities = scope_capabilities(mso_horiz, mso_vertical)

def trigger_v(state):
    return int(0x200-(state.trigger_voltage+state.vertical_offset)*(932/40))

def trigger_v_lsb(state):
    return trigger_v(state)&0xFF

def trigger_setup(state):
    a = 0
    if state.trigger == "rising":
        a |= (0<<5) | (0<<2)
    elif state.trigger == "falling":
        a |= (0<<5) | (1<<2)
    return trigger_v(state)>>8 | a

def trigger_h(state):
    return int(1000*state.trigger_position/100 + mso_horiz_offset[state.time_per_div])

def trigger_h_lsb(state):
    return trigger_h(state)&0xFF

def trigger_h_msb(state):
    return trigger_h(state)>>8

def horiz_a(state):
    return mso_horiz_reg[state.time_per_div][0]

def horiz_b(state):
    return mso_horiz_reg[state.time_per_div][1]

def pulse_trig_w(state):
    return 3

def vert_off(state):
    return int(0x159-(state.vertical_offset*16.6))

def vert_off_lsb(state):
    return vert_off(state)&0xFF

def vert_off_msb(state):
    return vert_off(state)>>8

def misc(state):
    if state.time_per_div >= 20e-3:
        return 1<<5
    else:
        return 0

MSO_QUERY_DATA    = 0x1
MSO_QUERY_TRIGGER = 0x2
MSO_TRIGGER_V_LSB = 0x3
MSO_TRIGGER_SETUP = 0x4
MSO_TRIGGER_H_LSB = 0x7
MSO_TRIGGER_H_MSB = 0x8
MSO_HORIZ_A       = 0x9
MSO_HORIZ_B       = 0xA
MSO_PULSE_TRIG_W  = 0xB
MSO_VERT_OFF_MSB  = 0xC
MSO_VERT_OFF_LSB  = 0xD
MSO_TRIGGER       = 0xE
MSO_MISC          = 0xF

class mso:
    def __init__(self, port):
        self.ser = mso_serial(port)
        self.state = None

    def set_state(self, state):
        self.state = state

    def reset(self):
        self.ser.flush()
        self.ser.send_commands([(MSO_TRIGGER, 0x40), (MSO_TRIGGER, 0x00)])
        self.ser.send_commands([(MSO_QUERY_TRIGGER, 0)], response=1)
        self.ser.send_commands([(MSO_TRIGGER, 0x11)], delay=1000)
        self.ser.send_commands([(MSO_QUERY_TRIGGER, 0)], response=1)

    def run(self):
        self.ser.send_commands([(MSO_TRIGGER, 0x91), (MSO_TRIGGER, 0x92), (MSO_TRIGGER, 0x90)])

    def stop(self):
        self.ser.send_commands([(MSO_TRIGGER, 0x91)])

    def force_trigger(self):
        self.ser.send_commands([(MSO_TRIGGER, 0x98), (MSO_TRIGGER, 0x90)])

    def configure_all(self):
        commands = [
                    (MSO_HORIZ_A,        horiz_a(self.state)),
                    (MSO_HORIZ_B,        horiz_b(self.state)),
                    ]
        self.ser.send_commands(commands)
        commands = [
                    (MSO_VERT_OFF_MSB,  vert_off_msb(self.state)),
                    (MSO_VERT_OFF_LSB,  vert_off_lsb(self.state)),
                    (MSO_TRIGGER, 0x30),
                    ]
        #self.ser.send_commands(commands)
        #commands = [
        #            (0xC, 0x8F),
        #            (0xD, 0xFF),
        #            (0xE, 0x30),
        #            ]
        self.ser.send_commands(commands)
        commands = [
                    (MSO_TRIGGER_V_LSB, trigger_v_lsb(self.state)),
                    (MSO_TRIGGER_SETUP, trigger_setup(self.state)),
                    (MSO_PULSE_TRIG_W,  pulse_trig_w(self.state)),
        #            (0x5, 0x01),
        #            (0x6, 0xFC),
        #            (0xF, 0x02),
        #            (0x0, 0xFF),
        #            (0x1, 0xFF),
        #            (0x2, 0xFF),
        #            (0x3, 0xFF),
        #            (0x4, 0xFF),
        #            (0x5, 0xFF),
        #            (0x6, 0xFF),
        #            (0x7, 0xFF),
        #            (0x8, 0x00),
        #            (0xF, 0x00),
                    ]
        self.ser.send_commands(commands)
        commands = [
                    (MSO_TRIGGER_H_LSB, trigger_h_lsb(self.state)),
                    (MSO_TRIGGER_H_MSB, trigger_h_msb(self.state)),
                    ]
        self.ser.send_commands(commands)
        commands = [
                    (MSO_MISC, misc(self.state)),
                    ]
        self.ser.send_commands(commands)
        time.sleep(.5)
        self.ser.flush()

    def get_trigger_status(self):
        trigger = self.ser.send_commands([(MSO_QUERY_TRIGGER, 0)], delay=1000, response=1)
        if trigger == "6":
            return "data ready"
        elif trigger == "5":
            return "triggered"
        elif trigger == "4":
            return "waiting"
        elif trigger == "3":
            return "pretrigger"
        elif trigger == "1":
            return "stopped"
        else:
            raise Exception("Unknown trigger %s" % trigger)

    def wait_for_trigger(self):
        while True:
            if self.get_trigger_status() == "data ready":
                return

    def read_data(self):
        ret = self.ser.send_commands([(MSO_QUERY_DATA, 0)], delay=1000, response=3*1024)
        data = parse_in(ret)
        data = data[1:1001]
        x_offset = -(self.state.trigger_position/10)*self.state.time_per_div
        x_scale = self.state.time_per_div*10/1000
        y_offset = -(self.state.vertical_offset)
        return [(x[0]*x_scale+x_offset, x[1]+y_offset, x[2]) for x in data]

    def get_capabilities(self):
        return mso_capabilities

class mso_serial:
    def __init__(self, port):
        if port == "libusb":
            from cp210x import cp210x
            self.ser = cp210x(0x3195, 0xf190);
        else:
            import serial
            self.ser = serial.Serial(port, baudrate=460800)

#        self.ser.open()
#        print self.ser

    def flush(self):
        pass
#        self.ser.flushOutput()
#        self.ser.flushInput()

    def send_commands(self, cmds, delay=10, response=0):
        s = to_cmd("".join((to_cmd_pair(cmd[0], cmd[1]) for cmd in cmds)))
        write_serial(self.ser, s)
        if response>0:
            s = read_serial(self.ser, response, delay)
            return s
        else:
            time.sleep(delay/1000.0)
            return None

