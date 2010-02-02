import threading
import time

class scope_interface:
    def __init__(self, scope_class, port):
        self.scope = scope_class(port)
        self.thread = threading.Thread(target=self.main_loop)

        # Background thread variables
        self.quit = False   # Can be set to True by GUI thread

        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()

        self.state_changed = True
        self.AUTO, self.NORMAL, self.SINGLE = range(3)
        self.trigger_mode = self.AUTO
        
        self.trigger_state_changed_callback = None
        
        self.thread.start()

    def set_data_callback(self, callback): self.data_callback = callback
    def set_trigger_state_changed_callback(self, callback): self.trigger_state_changed_callback = callback

    # Functions called within GUI thread
    def get_capabilities(self):
        return self.scope.get_capabilities()

    def set_state(self, state):
        self.stop()
        self.scope.set_state(state.copy())
        self.auto_delay = state.time_per_div*10
        self.state_changed = True

    def set_trigger_mode(self, mode):
        self.trigger_mode = mode
        pass

    def start(self):
        self.stop_event.clear()
        self.start_event.set()

    def stop(self):
        self.start_event.clear()
        self.stop_event.set()
        self.stopped_event.wait()

    # Background thread
    def main_loop(self):
        self.scope.reset()

        while not self.quit:
            if not self.start_event.isSet():
                self.scope.stop()
                if self.trigger_state_changed_callback:
                    self.trigger_state_changed_callback("stopped")
                self.stopped_event.set()
                self.start_event.wait()
                self.stopped_event.clear()
            else:
                if self.state_changed == True:
                    self.scope.configure_all()
                    self.state_changed = False
                trigger_start_time = time.time()
                self.scope.run()
                last_trigger_status = None
                while self.start_event.isSet():
                    trigger = self.scope.get_trigger_status()
                    if trigger != last_trigger_status:
                        self.trigger_state_changed_callback(trigger)
                        last_trigger_status = trigger
                    if trigger == "data ready":
                        data = self.scope.read_data()
                        self.data_callback(data)
                        if self.trigger_mode == self.SINGLE:
                            self.start_event.clear()
                        else:
                            self.stop_event.wait(0.125)
                            trigger_start_time = time.time()
                            self.scope.run()
                    elif trigger == "waiting":
                        if self.trigger_mode == self.AUTO and time.time() - trigger_start_time > self.auto_delay:
                            self.scope.force_trigger()
                            last_trigger_status = "auto"
                            self.trigger_state_changed_callback("auto")
                        else:
                            self.stop_event.wait(0.125)
                    elif trigger == "pretrigger":
                        pass
                    elif trigger == "triggered":
                        pass
                    elif trigger == "stopped":
                        pass
                    else:
                        print "Unknown trigger %s" % trigger
