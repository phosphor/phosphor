import re
import gtk
import gobject

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
    if m.group("units") is not None and m.group("units") != units:
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
