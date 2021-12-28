from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from pylsl import StreamInfo, StreamOutlet
from pythonosc.udp_client import SimpleUDPClient
import numpy as np

# TODO: change interval of recording to ms

# UDP details
IP = "127.0.0.1"
CLIENT_PORT = 2222
SERVER_PORT = 2223

# Determines how many different touch detections can be realized by the Max machine as different channels
CHANNELS = 2

# The shape of the grid
GRID_dict = {
                "Circular" : 1,
                "Rectangle" : 2
            }

# The origin of the grid
ORIGIN_dict = {
                "Bottom_left" : [0.0, 0.0],
                "Center" : [0.5, 0.5],
                "Center_bottom" : [0.5, 0],
            }

# The actual parameters fed into the machine
ORIGIN = "Bottom_left"
GRID = "Rectangle"
RANDOM = False
parameters = [ORIGIN, GRID, RANDOM]


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

    def __init__(self, origin, grid, random):
        self.id = -1
        self.pos = [0, 0]
        self.switch = False
        self.origin = ORIGIN_dict[origin]
        self.grid = GRID_dict[grid]
        self.origin_string = origin
        self.grid_string = grid
        self.random = random

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

    def circular_rep(self):
        # 'raw' euclidean distance of the position from the origin
        x = self.pos[0] - self.origin[0]
        y = self.pos[1] - self.origin[1]

        # calculate normalized radius. Normalization done by stretching the maximum value to 1.
        if self.origin_string == "Center":
            # origin = (0.5, 0.5) ==>> max value = sqrt(0.5)
            radius = np.sqrt(2 * (x ** 2 + y ** 2))
        elif self.origin_string == "Center_bottom":
            # origin = (0.5, 0) ==>> max value = sqrt(5/4)
            radius = np.sqrt(4 / 5 * (x ** 2 + y ** 2))
        else:
            # origin = (0, 0) ==>> max value = sqrt(2)
            radius = np.sqrt((x ** 2 + y ** 2) / 2)

        tan = 0 if x == 0 else np.abs(np.tanh(y / x))
        return [radius, tan]

    def generate_data(self):
        if self.grid_string == "Circular":
            return self.circular_rep()

        # else => Origin maybe not CENTER
        # If origin is center, the normalization is just *2 for both axis
        elif self.origin_string == "Center":
            return [2 * np.abs(self.pos[0] - self.origin[0]), 2 * np.abs(self.pos[1] - self.origin[1])]

        # If origin is X center, Y bottom, the normalization is *2 only for X axis
        elif self.origin_string == "Center_bottom":
            return [2 * np.abs(self.pos[0] - self.origin[0]), np.abs(self.pos[1] - self.origin[1])]

        # else => origin is default (bottom left), no normalization required
        else:
            return self.pos

    def random_data(self):
        mean1, sd1 = self.pos[0], np.abs(self.pos[1])
        mean2, sd2 = self.pos[1], np.abs(self.pos[0])
        x = np.random.normal(mean1, sd1)
        y = np.random.normal(mean2, sd2)

        return [np.abs(min(1.0, x)), np.abs(min(1.0, y))]

    def get_data(self):
        if not self.switch:
            return [0, 0]

        if self.random:
            return self.random_data()

        else:
            return self.generate_data()

    def __repr__(self):
        return "Id :{}, Active?: {},Position: {}".format(self.id, self.switch, self.pos)


class UDPclient:
    """
    Object represents the connection to the UDP, which holds for the communication with Max8.
    """

    def __init__(self):
        self.client = SimpleUDPClient(IP, CLIENT_PORT)

    def broadcast(self, data):
        self.client.send_message("/some/address", data)


class Printer:
    """
    Broadcaster to the screen
    """

    def broadcast(self, data):
        print(data)

class LSLbroadcast:
    """
    A wrapper for a broadcasting LSL connection
    """
    def __init__(self, channels, session_info_LSL):
        self.channels = channels
        self.conn = self.establishLSL(session_info_LSL)

    def establishLSL(self, session_info_LSL):
        self.info = StreamInfo(name="Touch events", type=session_info_LSL, channel_count=len(self.channels) * 2)
        self.outlet = StreamOutlet(self.info)
        print("-------------Outlet stream was created, LSL connections established successfully------------")
        print("-------------info type string: %s------------" % session_info_LSL)

    def broadcast(self, data):
        """
        Broadcasting the data to LSL connection
        """
        self.outlet.push_sample(data)


class DataBroadcaster:

    def __init__(self, channels):
        self.channels = channels
        self.LSLconn = LSLbroadcast(channels, self.generate_type_string())
        self.udp_client = UDPclient()
        self.printer = Printer()

    def generate_type_string(self):
        return "Origin: " + parameters[0] +\
               ", " + "Grid: " + parameters[1] +\
               ", " + "Random Sound: " + str(parameters[2])

    def broadcast(self, *args):
        """
        Broadcasting the data from channels to the customers.
        1st customer is LSL connection
        2nd customer is UDP client
        Data is a list of float numbers, in the shape:
        (Time, Channels), where "Time" is the time stamp and channels is the number of channels defined by the run.
        In order to plot the data correctly, a transposition needs to be applied
        """
        # Prepare data
        toUDP = []
        toLSL = []
        for ch in self.channels:
            toLSL += ch.get_pos()
            toUDP += ch.get_data()

        # Broadcasting the toLSL data to LSLconn
        self.LSLconn.broadcast(toLSL)

        # Broadcasting the toUDP data to UDPclient
        self.udp_client.broadcast(toUDP)


class TouchInput(Widget):

    def __init__(self, channels, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.waiting_ch = self.waiting_channel = TouchEvent(*parameters)

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
        self.channels = [TouchEvent(*parameters) for ch in range(CHANNELS)]
        self.broadcaster = DataBroadcaster(self.channels)

    def build(self):
        Clock.schedule_interval(self.broadcaster.broadcast, 0.001)
        return TouchInput(self.channels)


if __name__ == "__main__":
    MyApp().run()
