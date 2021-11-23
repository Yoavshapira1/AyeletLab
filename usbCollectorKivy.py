from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy import examples_dir
import multiprocessing
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from osc4py3 import oscmethod as osm


IP = "132.64.196.174"
OSC_PORT = 12001
TOUCH_SCREEN = "WM_MotionEvent"
movements = {}


    ########################## OSC protocol #############################

def handlerfunction(s, x, y):
    # Will receive message data unpacked in s, x, y
    pass

def handlerfunction2(address, s, x, y):
    # Will receive message address, and message data flattened in s, x, y
    pass

def recieve_from_OSC():
    # Start the system.
    osc_startup()

    # Make server channels to receive packets.
    osc_udp_server("192.168.0.0", 3721, "aservername")
    osc_udp_server("0.0.0.0", 3724, "anotherserver")

    # Associate Python functions with message address patterns, using default
    # argument scheme OSCARG_DATAUNPACK.
    osc_method("/test/*", handlerfunction)
    # Too, but request the message address pattern before in argscheme
    osc_method("/test/*", handlerfunction2, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)

    # Periodically call osc4py3 processing method in your event loop.
    finished = False
    while not finished:
        # …
        osc_process()
        # …

    # Properly close the system.
    osc_terminate()

def send_to_OSC():
    # Start the system.
    osc_startup()

    # Make client channels to send packets.
    osc_udp_client("192.168.0.4", 2781, "aclientname")

    # Build a simple message and send it.
    msg = oscbuildparse.OSCMessage("/test/me", ",sif", ["text", 672, 8.871])
    osc_send(msg, "aclientname")

    # Build a message with autodetection of data types, and send it.
    msg = oscbuildparse.OSCMessage("/test/me", None, ["text", 672, 8.871])
    osc_send(msg, "aclientname")

    # Buils a complete bundle, and postpone its executions by 10 sec.
    exectime = time.time() + 10  # execute in 10 seconds
    msg1 = oscbuildparse.OSCMessage("/sound/levels", None, [1, 5, 3])
    msg2 = oscbuildparse.OSCMessage("/sound/bits", None, [32])
    msg3 = oscbuildparse.OSCMessage("/sound/freq", None, [42000])
    bun = oscbuildparse.OSCBundle(oscbuildparse.unixtime2timetag(exectime),
                                  [msg1, msg2, msg3])
    osc_send(bun, "aclientname")

    # Periodically call osc4py3 processing method in your event loop.
    finished = False
    while not finished:
        # You can send OSC messages from your event loop too…
        # …
        osc_process()
        # …

    # Properly close the system.
    osc_terminate()

    ########################## USB COLLECT ###############################

class TouchInput(Widget):

    def on_touch_down(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements[touch.id] = []
            print(touch.id, touch.sx, touch.sy)

    def on_touch_move(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements[touch.id].append((touch.sx, touch.sy))
            print(touch.id, touch.sx, touch.sy)

    def on_touch_up(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements.pop(touch.id)
            print(touch.id, touch.sx, touch.sy)

class MyApp(App):
    def build(self):
        return TouchInput()

if __name__ == "__main__":
    # Window.bind(on_motion=on_motion)
    MyApp().run()
