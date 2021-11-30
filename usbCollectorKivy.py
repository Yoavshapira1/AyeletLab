import time
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from osc4py3 import oscmethod as osm
from pylsl import StreamInfo, StreamOutlet
from matplotlib import pyplot as plt, animation

# UPD details
IP = "127.0.0.1"
OSC_CLIENT = 12001
OSC_SERVER = 12002

# Determines how many different touch detections can be realized by the Max machine as different channels
CHANNELS = 1


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

class TouchEvent:
    """
    This class represents a single motion event on the screen
    """

    def __init__(self):
        self.id = -1
        self.pos = (0, 0)
        self.switch = False

    def activate(self):
        self.switch = True

    def deactivate(self):
        self.switch = False

    def move(self, pos):
        self.pos = pos

    def rename_id(self, id):
        self.id = id

    def isActive(self):
        return self.switch

    def id(self):
        return self.id

    def pos(self):
        return self.pos

    def data(self):
        if not self.switch:
            return [-1, -1]
        return [self.pos[0], self.pos[1]]


    def __repr__(self):
        return "Id :{}, Active?: {},Position: {}".format(self.id, self.switch, self.pos)

class costumer():

    def __init__(self):
        self.fig = plt.figure()
        self.x = []
        self.y = []
        self.anim = animation.FuncAnimation(self.fig, self.animate, frames=100, interval=1000)

    def animate(n):
        line, = plt.plot(self.x[:n], self.y[:n], color='g')
        return line,

    plt.show()



        plt.show()

class LSLconnection:

    def __init__(self, channels):
        self.channels = channels
        self.info = StreamInfo(name="Touch events", source_id='myuid', channel_count=len(channels) * 2)
        self.outlet = StreamOutlet(self.info)
        print("-------------Outlet stream was created, LSL connections established successfully------------")

        self.costumer = costumer()

    def broadcast(self, *args):

        # Broadcasting to LSL
        to_broadcast = []
        for ch in self.channels:
            to_broadcast += ch.data()
        self.outlet.push_sample(to_broadcast)

        # Broadcasting to another costumer
        self.costumer.broadcast(to_broadcast)


class TouchInput(Widget):

    def __init__(self, channels, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels

    # Name of the touch type that is to be detected as a touch event
    TOUCH_SCREEN = "wm_touch"

    def on_touch_down(self, touch):
        if touch.device != self.TOUCH_SCREEN:
            return
        for ch in self.channels:
            if not ch.isActive():
                ch.move((touch.sx, touch.sy))
                ch.rename_id(touch.id)
                ch.activate()
                break

    def on_touch_move(self, touch):
        if touch.device != self.TOUCH_SCREEN:
            return
        for ch in self.channels:
            if ch.id == touch.id:
                ch.move((touch.sx, touch.sy))
                break

    def on_touch_up(self, touch):
        if touch.device != self.TOUCH_SCREEN:
            return
        for ch in self.channels:
            if ch.id == touch.id:
                ch.deactivate()
                break


class MyApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channels = [TouchEvent() for ch in range(CHANNELS)]
        self.LSLconn = LSLconnection(self.channels)

    def build(self):
        Clock.schedule_interval(self.LSLconn.broadcast, 0.01)
        return TouchInput(self.channels)


if __name__ == "__main__":
    MyApp().run()
