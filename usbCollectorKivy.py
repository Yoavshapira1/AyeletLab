from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from pylsl import StreamInfo, StreamOutlet
from pythonosc.udp_client import SimpleUDPClient
import numpy as np

# UDP details
IP = "127.0.0.1"
CLIENT_PORT = 2222
SERVER_PORT = 2223

# Determines how many different touch detections can be realized by the Max machine as different channels
CHANNELS = 2

# The shape of the grid
CIRCULAR = 1
RECT = 2
GRID = RECT

# The origin of the grid
BOTTUM_LEFT = [0.0, 0.0]
CENTER = [0.5, 0.5]
ORIGIN = CENTER


    ########################## USB COLLECT ###############################

class TouchEvent:
    """
    This object represents a single touch on the touch screen.
    A touch event defined to start when a touch is detected till this very touch leaves the screen.
    It has the attributes:
        id: Unique id for the touch event.
        pos: The current position of the touch event. In case the switch is False, it holds the last position.
        switch: Activation boolean value, True if the event still occurring, meanly the touch is still on the screen,
        and False other wise.
    The data of an event equals to [*pos], unless it switched to False and then the data is equal to [-1,-1].
    """

    def __init__(self, origin, grid):
        self.id = -1
        self.pos = (0, 0)
        self.switch = False
        self.origin = origin
        self.grid = grid

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

    def get_id(self):
        return self.id

    def get_pos(self):
        return self.pos

    def generate_data(self):
        x = self.pos[0] - self.origin[0]
        y = self.pos[1] - self.origin[1]
        if self.grid == CIRCULAR:
            radius = np.sqrt(2*(x**2 + y**2))
            if x == 0:
                angel = np.pi / 2 if y > 0 else np.pi * (3/2)
            else:
                angel = np.arctan(y/x)
            return [radius, 0.5 + np.abs(np.sin(angel)*np.cos(angel))]
        return [0.5+np.abs(x), 0.5+np.abs(y)]


    def get_data(self):
        if not self.switch:
            return [-1, -1]
        return self.generate_data()

    def __repr__(self):
        return "Id :{}, Active?: {},Position: {}".format(self.id, self.switch, self.pos)

class UDPclient():
    """
    Object represents the connection to the UDP, which holds for the communication with Max8.
    """
    def __init__(self):
        self.client = SimpleUDPClient(IP, CLIENT_PORT)

    def broadcast(self, data):
        self.client.send_message("/some/address", data)

class Printer():
    """
    Object represents the connection to the UDP, which holds for the communication with Max8.
    """

    def broadcast(self, data):
        print(data)

class LSLconnection:

    def __init__(self, channels):
        self.channels = channels
        self.info = StreamInfo(name="Touch events", source_id='myuid', channel_count=len(channels) * 2)
        self.outlet = StreamOutlet(self.info)
        print("-------------Outlet stream was created, LSL connections established successfully------------")

        self.costumer = UDPclient()
        # self.costumer = Printer()

    def broadcast(self, *args):
        """
        Broadcasting the data from channels to the customers.
        1st customer is LSL connection
        2nd customer is UDP client
        Data is a list of float numbers, in the shape:
        (Time, Channels), where "Time" is the time stamp and channels is the number of channels defined by the run.
        In order to plot the data correctly, a transposition needs to be applied
        """
        # Broadcasting to LSL
        to_broadcast = []
        for ch in self.channels:
            to_broadcast += ch.get_data()
        self.outlet.push_sample(to_broadcast)

        # Broadcasting to another costumer
        self.costumer.broadcast(to_broadcast)


class TouchInput(Widget):

    def __init__(self, channels, waiting_ch, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.waiting_ch = waiting_ch

    # Name of the touch type that is to be detected as a touch event
    TOUCH_SCREEN = "wm_touch"

    def on_touch_down(self, touch):
        # If not touch screen type, do nothing
        if touch.device == self.TOUCH_SCREEN:

            # Check if any available channel
            for ch in [*self.channels, self.waiting_ch]:
                if not ch.isActive():
                    ch.move((touch.sx, touch.sy))
                    ch.rename_id(touch.id)
                    ch.activate()
                    break

    def on_touch_move(self, touch):
        if touch.device == self.TOUCH_SCREEN:
            for ch in [*self.channels, self.waiting_ch]:
                if ch.get_id() == touch.id:
                    ch.move((touch.sx, touch.sy))
                    break

    def on_touch_up(self, touch):
        if touch.device != self.TOUCH_SCREEN:
            return
        for ch in self.channels:
            if ch.get_id() == touch.id:
                if self.waiting_ch.isActive():
                    ch.rename_id(self.waiting_ch.get_id())
                    ch.move(self.waiting_ch.get_pos())
                    ch.activate()
                    self.waiting_ch.deactivate()
                else:
                    ch.deactivate()
                break
        if self.waiting_ch.get_id() == touch.id:
            self.waiting_ch.deactivate()
            return

class MyApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channels = [TouchEvent(ORIGIN, GRID) for ch in range(CHANNELS)]
        self.waiting_channel = TouchEvent(ORIGIN, GRID)
        self.LSLconn = LSLconnection(self.channels)

    def build(self):
        Clock.schedule_interval(self.LSLconn.broadcast, 0.01)
        return TouchInput(self.channels, self.waiting_channel)


if __name__ == "__main__":
    MyApp().run()
