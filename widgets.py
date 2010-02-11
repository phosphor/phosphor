import re
import gtk
import gobject
import matplotlib
matplotlib.use('GTKAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg

un_pretty_print_re_string = r"""
^\s*                         # Ignore initial whitespace
(?P<neg>-)?                  # Possible -
(?P<num>[0-9\.]+)            # Floating point number
\s*                          # Ignore whitespace
(?P<mult>[pnu\u03bcmkM])?    # Possible unit prefix
(?P<units>(s|v|hz))?         # Possible units
\s*$                         # Ignore trailing whitespace
"""
un_pretty_print_re = re.compile(un_pretty_print_re_string, re.I|re.X)
def un_pretty_print(s, units):
    m = un_pretty_print_re.match(s)
    if m is None:
        return None

    neg = 1
    mult = 1
    if m.group("neg") == "-":
        neg = -1
    if m.group("mult") == "p" or m.group("mult") == "P":
        mult = 1e-12
    elif m.group("mult") == "n" or m.group("mult") == "N":
        mult = 1e-9
    if m.group("mult") == "u" or m.group("mult") == "U" or m.group("mult") == u"\u03bc":
        mult = 1e-6
    if m.group("mult") == "m":
        mult = 1e-3
    if m.group("mult") == "k" or m.group("mult") == "K":
        mult = 1e3
    if m.group("mult") == "M":
        mult = 1e6
    if m.group("units") is not None and m.group("units").lower() != units.lower():
        return None
    return float(m.group("num")) * neg * mult

def pretty_print(val, units):
    div = 1
    neg = ""
    s=""
    if (val < 0):
        val = -val
        neg = "-"

    if (val < 1e-12):
        val = 0
        s = ""
    elif val < 1e-9:
        div = 1e-12
        s = "p"
    elif val < 1e-6:
        div = 1e-9
        s = "n"
    elif val < 1e-3:
        div = 1e-6
        s = u"\u03bc"
    elif val < 1:
        div = 1e-3
        s = "m"
    elif val < 1e3:
        pass
    elif val < 1e6:
        div = 1e3
        s = "k"
    elif val < 1e9:
        div = 1e6
        s = "M"
    else:
        raise Exception("Value too large: %d" % val)
    return "%s%g %s%s" % (neg, val/div, s, units)

class ComboBoxButtonDataModel:
    def __init__(self, wTree, widget, editable, values, units, changed_callback, min_val=None, max_val=None):
        self.widget = widget
        self.editable = editable
        self.combo_box = wTree.get_widget(widget)
        #wTree.signal_connect("on_%s_editing_done" % widget, self.editing_done)
        self.values = sorted(values)
        self.units = units
        self.changed_callback = changed_callback
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        for v in self.values:
            liststore.append([pretty_print(v, units)])
        self.combo_box.set_model(liststore)
        self.combo_box.set_text_column(0)
        self.combo_box.set_active(0)
        self.value = self.values[0]
        if min_val is None: min_val = min(self.values)
        if max_val is None: max_val = max(self.values)
        self.min = min_val
        self.max = max_val

        self.combo_box.child.connect("activate", self.editing_done)
        self.combo_box.child.connect("focus-out-event", self.editing_done)
        wTree.signal_connect("on_%s_up_clicked" % widget, self.up_clicked)
        wTree.signal_connect("on_%s_down_clicked" % widget, self.down_clicked)
        wTree.signal_connect("on_%s_changed" % widget, self.changed)

    def get_closest_below(self, value):
        for i in range(len(self.values)):
            if self.values[len(self.values)-1-i] <= value:
                return len(self.values)-1-i

    def get_closest_above(self, value):
        for i in range(len(self.values)):
            if self.values[i] >= value:
                return i

    def up_clicked(self, button):
        i = self.get_closest_below(self.value)
        if i < len(self.values)-1:
            self.combo_box.set_active(i+1)
            #self.changed_callback(self)

    def down_clicked(self, button):
        i = self.get_closest_above(self.value)
        if i > 0:
            self.combo_box.set_active(i-1)
            #self.changed_callback(self)

    def changed(self, combo_box):
        if self.combo_box.get_active() != -1:
            i = self.combo_box.get_active()
            self.value = self.values[i]
            self.changed_callback(self)

    def editing_done(self, combo_box, a=None):
        v = un_pretty_print(self.combo_box.child.get_text(), self.units)
        if v is None:
            v = self.value
        if v < self.min:
            v = self.min
        elif v > self.max:
            v = self.max
        i = self.get_closest_below(v)
        if i is None: i = 0
        if v != self.values[i] and not self.editable:
            return
        if v == self.values[i]:
            self.combo_box.set_active(i)
        else:
            self.combo_box.child.set_text(pretty_print(v, self.units))
        self.value = v
        self.changed_callback(self)


class CursorDataModel:
    def __init__(self, wTree, widget, plot, dir, units, changed_callback):
        self.widget = widget
        self.plot = plot
        self.dir = dir
        self.units = units
        self.changed_callback = changed_callback
    
        self.value = None
        self.enabled = True
        
        self.textbox = wTree.get_widget(widget)
        self.textbox.connect("activate", self.editing_done)
        self.textbox.connect("focus-out-event", self.editing_done)
    
    def set(self, value):
        self.value = value
        print value
        self.changed_callback(self)
    
    def editing_done(self, textbox, a=None):
        print textbox.get_text()
        v = un_pretty_print(textbox.get_text(), self.units)
        if v is None:
            v = self.value
        self.value = v
        self.changed_callback(self)

class LinkedCursorDataModel:
    def __init__(self, wTree, widget, plot, dir, units, changed_callback):
        self.widget = widget
        self.plot = plot
        self.dir = dir
        self.units = units
        self.changed_callback = changed_callback
    
        self.a = CursorDataModel(wTree, "%s_a" % widget, plot, dir, units, self.changed)
        self.b = CursorDataModel(wTree, "%s_b" % widget, plot, dir, units, self.changed)
        self.delta = CursorDataModel(wTree, "%s_delta" % widget, plot, dir, units, self.changed)
        
    def changed(self, a):
        print self.a.value
        print self.b.value
        print self.delta.value
        self.changed_callback(self)

class PlotWidget:
    def __init__(self, wTree, widget):
        figure = Figure(figsize=(6,4), dpi=72)
        axes = figure.add_subplot(1,1,1)
        canvas = FigureCanvasGTKAgg(figure)
        canvas.show()
        canvas.mpl_connect('pick_event', self.pick_handler)
        canvas.mpl_connect('motion_notify_event', self.motion_handler)
        canvas.mpl_connect('button_release_event', self.release_handler)
        canvas.mpl_connect('button_press_event', self.press_handler)
        graphview = wTree.get_widget(widget)
        graphview.add_with_viewport(canvas)
        self.figure = figure
        self.canvas = canvas
        self.axes = axes
        self.plot_line = self.axes.plot([], [], 'b-', animated=True)[0]
        self.cursors = []
        self.picked = None
        self.data = []
    
    def pick_handler(self, event):
        print "pick", a
        self.picked = event.artist

    def motion_handler(self, event):
        if self.picked is not None:
            if self.picked in self.cursors:
                if self.dir == "h":
                    self.model.set(event.y)
                else:
                    self.model.set(event.x)

    def press_handler(self, a):
        print "press", a

    def release_handler(self, a):
        print "release", a
        self.picked = None


    def update_axes(self, time_per_div, trigger_position, volts_per_div, vertical_offset, trigger_voltage):
        x_min =   -(trigger_position/10)*time_per_div
        x_max = (10-trigger_position/10)*time_per_div
        x_ticks = (x_max-x_min)/10

        y_min = -volts_per_div*5 - vertical_offset
        y_max =  volts_per_div*5 - vertical_offset
        y_ticks = (y_max-y_min)/10
        
        self.axes.cla()
        print "clear axes"
        self.axes.set_xticks([x_min+x_ticks*x for x in range(11)])
        self.axes.set_xticklabels([pretty_print(x,"s") for x in self.axes.get_xticks()])
        self.axes.set_yticks([y_min+y_ticks*y for y in range(11)])
        self.axes.set_yticklabels([pretty_print(y,"V") for y in self.axes.get_yticks()])
        self.axes.grid(True)
        self.axes.axhline(trigger_voltage, linestyle='--', color='r', picker=True)
        self.axes.axhline(0, linestyle='-', color='k', picker=True)
        self.axes.axvline(0, linestyle='--', color='r', picker=True)
        self.axes.axis([x_min, x_max, y_min, y_max])
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.canvas.restore_region(self.background)
        gobject.idle_add(self.draw_plot)
        
    def plot(self, data):
        self.data = data
        gobject.idle_add(self.draw_plot)

    def draw_plot(self):
        print "draw_plot"
        self.canvas.restore_region(self.background)
        self.plot_line.set_data([d[0] for d in self.data], [d[1] for d in self.data])
        self.axes.draw_artist(self.plot_line)
        for x in self.cursors:
            if x.model.enabled:
                print x
                self.axes.draw_artist(x)
        self.canvas.blit(self.axes.bbox)
        return False

    def add_cursor(self, cursor_model, dir, linestyle='-', color='b'):
        if dir == "h":
            line = self.axes.axhline(cursor_model.value, linestyle=linestyle, color=color, picker=True, animated=True)
        else:
            line = self.axes.axvline(cursor_model.value, linestyle=linestyle, color=color, picker=True, animated=True)
        line.model = cursor_model
        line.dir = dir
        self.cursors.append(line)
