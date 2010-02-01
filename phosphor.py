#!/usr/bin/python

from mso19 import mso_interface
import sys
import pygtk
pygtk.require('2.0')
import gtk.glade
import gobject
gtk.gdk.threads_init()

import matplotlib
matplotlib.use('GTK')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk import FigureCanvasGTK
import scope
import widgets

class appGui:
    def __init__(self, s, m):
        self.scope_state = s
        self.mso = m
        self.capabilities = m.get_capabilities()
        self.run_state = 0
        self.state_changed = False
        self.trigger_mode = self.mso.AUTO
        self.scope_state.time_per_div = self.capabilities.horiz.vals[0]
        self.scope_state.volts_per_div = self.capabilities.vertical.vals[0]

        m.set_data_callback(lambda x: gobject.idle_add(self.data_callback, x))
        m.set_trigger_state_changed_callback(lambda x: gobject.idle_add(self.trigger_changed_callback, x))

        gladefile = "phosphor.glade"
        self.windowname = "window"
        self.wTree = gtk.glade.XML(gladefile, self.windowname)
        self.statusbar = self.wTree.get_widget("statusbar")
        self.statusbar_contextid = self.statusbar.get_context_id("main")

        self.time_per_div = widgets.ComboBoxButtonDataModel(self.wTree, "horiz", False, self.capabilities.horiz.vals, "s", self.update_state)
        self.volts_per_div = widgets.ComboBoxButtonDataModel(self.wTree, "vertical", True, self.capabilities.vertical.vals, "V", self.update_state)
        self.vertical_offset = widgets.ComboBoxButtonDataModel(self.wTree, "vertical_offset", True, [0.0], "V", self.update_state, -20.0, 20.0)
        self.trigger_position = widgets.ComboBoxButtonDataModel(self.wTree, "trigger_pos", True, [0.0, 25.0, 50.0, 75.0, 100.0], "%", self.update_state)
        self.trigger_voltage = widgets.ComboBoxButtonDataModel(self.wTree, "trigger_voltage", True, [0.0], "V", self.update_state, -20.0, 20.0)
        self.init_plot()

        dic = {
            "on_window_destroy" : gtk.main_quit,
            "on_start_stop_clicked" : self.start_stop_clicked,
            "on_trigger_mode_auto_group_changed"  : self.on_trigger_mode_auto_group_changed,
        }
        self.wTree.signal_autoconnect(dic)

    def update_state(self, cause):
        self.scope_state.volts_per_div = self.volts_per_div.value
        self.scope_state.time_per_div = self.time_per_div.value
        self.scope_state.trigger_position = self.trigger_position.value
        self.scope_state.vertical_offset = self.vertical_offset.value
        self.scope_state.trigger_voltage = self.trigger_voltage.value
        self.state_changed = True
        if self.run_state == 1:
            self.mso.stop()
            self.mso.set_state(self.scope_state)
            self.mso.start()

    def data_callback(self, data):
        self.plot(data)

    def trigger_changed_callback(self, trigger):
        self.statusbar.pop(self.statusbar_contextid)
        self.statusbar.push(self.statusbar_contextid, trigger)
        if trigger == "stopped" and self.run_state == 1 and self.trigger_mode == self.mso.SINGLE:
            self.run_state = 0
            icon = self.wTree.get_widget("start_stop_icon")
            icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)

    def start_stop_clicked(self, a):
        icon = self.wTree.get_widget("start_stop_icon")
        if self.run_state == 0:
            self.mso.set_state(self.scope_state)
            self.mso.start()
            self.run_state = 1
            icon.set_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON)
        else:
            self.mso.stop()
            self.run_state = 0
            icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)

    def on_trigger_mode_auto_group_changed(self, a):
        if a.get_active():
            if a == self.wTree.get_widget("trigger_mode_auto"):
                self.trigger_mode = self.mso.AUTO
            elif a == self.wTree.get_widget("trigger_mode_single"):
                self.trigger_mode = self.mso.SINGLE
            elif a == self.wTree.get_widget("trigger_mode_normal"):
                self.trigger_mode = self.mso.NORMAL
            else:
                raise Exception("Unknown radio button %s" % a)
            self.mso.set_trigger_mode(self.trigger_mode)

    def on_trigger_pos_down_clicked(self, a):
        pass
    def on_trigger_pos_up_clicked(self, a):
        pass
    def on_trigger_pos_changed(self, a):
        pass

    def on_trigger_voltage_down_clicked(self, a):
        pass
    def on_trigger_voltage_up_clicked(self, a):
        pass
    def on_trigger_voltage_changed(self, a):
        pass

    def on_vertical_offset_down_clicked(self, a):
        pass
    def on_vertical_offset_up_clicked(self, a):
        pass
    def on_vertical_offset_changed(self, a):
        pass

    def init_plot(self):
        figure = Figure(figsize=(6,4), dpi=72)
        axes = figure.add_subplot(1,1,1)
        canvas = FigureCanvasGTK(figure)
        canvas.show()
        canvas.mpl_connect('pick_event', self.pick_handler)
        graphview = self.wTree.get_widget("graph")
        graphview.add_with_viewport(canvas)
        self.canvas = canvas
        self.axes = axes
        self.plot_line = None
        self.update_axes()
        self.plot([])

        #cursor_horiz_a = Cursor(self.axes, useblit=False)
        #cursor_horiz_b = Cursor(self.axes, useblit=False)

    def update_axes(self):
        x_min =   -(self.scope_state.trigger_position/10)*self.scope_state.time_per_div
        x_max = (10-self.scope_state.trigger_position/10)*self.scope_state.time_per_div
        x_ticks = (x_max-x_min)/10

        y_min = -self.scope_state.volts_per_div*5 - self.scope_state.vertical_offset
        y_max =  self.scope_state.volts_per_div*5 - self.scope_state.vertical_offset
        y_ticks = (y_max-y_min)/10

        self.axes.set_xticks([x_min+x_ticks*x for x in range(11)])
        self.axes.set_xticklabels([widgets.pretty_print(x,"s") for x in self.axes.get_xticks()])
        self.axes.set_yticks([y_min+y_ticks*y for y in range(11)])
        self.axes.set_yticklabels([widgets.pretty_print(y,"V") for y in self.axes.get_yticks()])
        self.axes.grid(True)
        self.axes.axhline(self.scope_state.trigger_voltage, linestyle='--', color='r', picker=True)
        self.axes.axhline(0, linestyle='-', color='k', picker=True)
        self.axes.axvline(0, linestyle='--', color='r', picker=True)
        self.axes.axis([x_min, x_max, y_min, y_max])

    def plot(self, data):
        #if self.plot_line in self.axes.lines:
        #    self.axes.lines.remove(self.plot_line)
        if self.state_changed:
            self.state_changed = False

        self.axes.cla()
        self.plot_line = self.axes.plot([d[0] for d in data], [d[1] for d in data], 'b-')[0]
        self.update_axes()
        self.canvas.draw_idle()
        #print "Plotted"

    def pick_handler(self, event):
        print event.artist
        print event.mouseevent
        print event.mouseevent.name

def main(argv=None):
    if argv is None:
        argv = sys.argv

    m = mso_interface(argv[1])
    s = scope.scope_state()
    app = appGui(s, m)
    gtk.main()

if __name__ == "__main__":
    sys.exit(main())
