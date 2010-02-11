#!/usr/bin/python

from mso19 import mso
from dummy import dummy_scope
from scope_interface import scope_interface
import sys
import pygtk
pygtk.require('2.0')
import gtk.glade
import gobject
gtk.gdk.threads_init()

import scope
import widgets

class appGui:
    def __init__(self, s, m):
        self.scope_state = s
        self.scope_interface = m
        self.capabilities = m.get_capabilities()
        self.run_state = 0
        self.state_changed = False
        self.trigger_mode = self.scope_interface.AUTO
        self.scope_state.time_per_div = self.capabilities.horiz.vals[0]
        self.scope_state.volts_per_div = self.capabilities.vertical.vals[0]
        self.data = []
        
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
        self.plot = widgets.PlotWidget(self.wTree, "graph")
        
        #self.cursor_horiz = widgets.LinkedCursorDataModel(self.wTree, "horizontal_cursor", self.plot, "horiz", "V", self.update_cursors)
        #self.cursor_vert = widgets.LinkedCursorDataModel(self.wTree, "vertical_cursor", self.plot, "vert", "s", self.update_cursors)
        #self.cursor_horiz.a.set(0)
        #self.cursor_horiz.b.set(.1)
        #self.cursor_vert.a.set(0)
        #self.cursor_vert.b.set(.1)
        #self.plot.add_cursor(self.cursor_horiz.a, "h", "-", "b")
        #self.plot.add_cursor(self.cursor_horiz.b, "h", "-", "b")
        #self.plot.add_cursor(self.cursor_vert.a, "v", "-", "b")
        #self.plot.add_cursor(self.cursor_vert.b, "v", "-", "b")

        dic = {
            "on_window_destroy" : gtk.main_quit,
            "on_start_stop_clicked" : self.start_stop_clicked,
            "on_trigger_mode_auto_group_changed"  : self.on_trigger_mode_auto_group_changed,
        }
        self.wTree.signal_autoconnect(dic)

    def update_cursors(self, cursor):
        pass

    def update_state(self, cause):
        self.scope_state.volts_per_div = self.volts_per_div.value
        self.scope_state.time_per_div = self.time_per_div.value
        self.scope_state.trigger_position = self.trigger_position.value
        self.scope_state.vertical_offset = self.vertical_offset.value
        self.scope_state.trigger_voltage = self.trigger_voltage.value
        self.plot.update_axes(self.scope_state.time_per_div, self.scope_state.trigger_position, self.scope_state.volts_per_div, self.scope_state.vertical_offset, self.scope_state.trigger_voltage)
        self.state_changed = True
        if self.run_state == 1:
            self.scope_interface.stop()
            self.scope_interface.set_state(self.scope_state)
            self.scope_interface.start()

    def data_callback(self, data):
        self.plot.plot(data)

    def trigger_changed_callback(self, trigger):
        self.statusbar.pop(self.statusbar_contextid)
        self.statusbar.push(self.statusbar_contextid, trigger)
        if trigger == "stopped" and self.run_state == 1 and self.trigger_mode == self.scope_interface.SINGLE:
            self.run_state = 0
            icon = self.wTree.get_widget("start_stop_icon")
            icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)

    def start_stop_clicked(self, a):
        icon = self.wTree.get_widget("start_stop_icon")
        if self.run_state == 0:
            self.scope_interface.set_state(self.scope_state)
            self.scope_interface.start()
            self.run_state = 1
            icon.set_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON)
        else:
            self.scope_interface.stop()
            self.run_state = 0
            icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)

    def on_trigger_mode_auto_group_changed(self, a):
        if a.get_active():
            if a == self.wTree.get_widget("trigger_mode_auto"):
                self.trigger_mode = self.scope_interface.AUTO
            elif a == self.wTree.get_widget("trigger_mode_single"):
                self.trigger_mode = self.scope_interface.SINGLE
            elif a == self.wTree.get_widget("trigger_mode_normal"):
                self.trigger_mode = self.scope_interface.NORMAL
            else:
                raise Exception("Unknown radio button %s" % a)
            self.scope_interface.set_trigger_mode(self.trigger_mode)

    def pick_handler(self, event):
        print event.artist
        print event.mouseevent
        print event.mouseevent.name

def main(argv=None):
    if argv is None:
        argv = sys.argv

    if argv[1] == "dummy":
        m = scope_interface(dummy_scope, None)
    else:
        m = scope_interface(mso, argv[1])
    s = scope.scope_state()
    app = appGui(s, m)
    gtk.main()

if __name__ == "__main__":
    sys.exit(main())
