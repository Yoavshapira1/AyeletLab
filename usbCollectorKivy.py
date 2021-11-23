import time
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy import examples_dir
import multiprocessing as mp
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from osc4py3 import oscmethod as osm
from pylsl import StreamInfo, StreamOutlet


IP = "132.64.196.174"
OSC_CLIENT = 12001
OSC_SERVER = 12002
TOUCH_SCREEN = "wm_touch"
movements = {0 : (0,0,0)}
ON = 1
OFF = 0


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
    osc_udp_server(IP, OSC_SERVER, "aservername")
    osc_udp_client(IP, OSC_CLIENT, "aclientname")

    # Associate Python functions with message address patterns, using default
    # argument scheme OSCARG_DATAUNPACK.
    osc_method("/test/*", handlerfunction)
    # Too, but request the message address pattern before in argscheme
    osc_method("/test/*", handlerfunction2, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)

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
        osc_process()

    # Properly close the system.
    osc_terminate()

def send_to_OSC():

    # Build a simple message and send it.
    msg = oscbuildparse.OSCMessage("/test/me", ",sif", ["text", 672, 8.871])
    osc_send(msg, "aclientname")

    # Build a message with autodetection of data types, and send it.
    msg = oscbuildparse.OSCMessage("/test/me", None, ["text", 672, 8.871])
    osc_send(msg, "aclientname")


    ########################## USB COLLECT ###############################

class TouchInput(Widget):

    def on_touch_down(self, touch):
        if touch.device == TOUCH_SCREEN:
            movements[0] = (touch.sx, touch.sy, ON)
            print(movements[0])

    def on_touch_move(self, touch):
        if touch.device == TOUCH_SCREEN:
            movements[0] = (touch.sx, touch.sy, ON)
            print(movements[0])

    def on_touch_up(self, touch):
        if touch.device == TOUCH_SCREEN:
            movements[0] = (touch.sx, touch.sy, OFF)
            print(movements[0])


class MyApp(App):

    def build(self):
        return TouchInput()

def send_data(id : int):
    print("worker ID: ", id)
    info = StreamInfo(name='Movements', source_id='myuid{}'.format(id), channel_count=3)
    print("worker {} stream info created".format(id))
    outlet = StreamOutlet(info)
    print("worker {} outlet info created".format(id))
    while True:
        outlet.push_sample(movements[id])
        print(movements[id])
        time.sleep(0.01)

if __name__ == "__main__":
    # Window.bind(on_motion=on_motion)

    MyApp().run()

    # data_to_LSL_process = mp.Process(target=send_data, args=(0,))
    # data_to_LSL_process.start()
    # app_process = mp.Process(target=MyApp.run)
    # app_process.start()

