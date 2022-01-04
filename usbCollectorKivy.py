import time

from kivy.app import App
from kivy.clock import Clock
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
PRINT_DATA = False

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
ORIGIN = "Center_bottom"
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
        # identity attributes
        self.id = -1
        self.origin = ORIGIN_dict[origin]
        self.grid = GRID_dict[grid]
        self.origin_string = origin
        self.grid_string = grid
        self.random = random

        # data-generating related
        self.dt = 0.01                      # The delta in time which used to calculate velocity and acceleration
        self.touch_time = 0
        self.max_norm = np.linalg.norm(np.array([1, 1]) - self.origin)
        self.reduce_time_threshold = self.max_norm / 50  # ||pos - prev_pos|| > threshold => reduce time_touch by half
        self.vel_normalization = 5          # An arbitrary number - was chosen by observations
        # initialize the values to zero
        self.deactivate()

    def activate(self):
        self.switch = True

    def deactivate(self):
        self.cur_pos = np.array([0, 0])
        self.prev_pos = np.array([0, 0])    # The previous position is been updated every dt
        self.prev_pos_time = time.time()
        self.touch_time = 0
        self.switch = False

    def move(self, pos):
        if time.time() - self.prev_pos_time > self.dt:
            if np.linalg.norm(self.cur_pos - self.prev_pos) > self.reduce_time_threshold:
                self.touch_time *= np.linalg.norm(self.cur_pos - self.prev_pos)
            self.prev_pos = self.cur_pos
            self.prev_pos_time = time.time()
            self.touch_time += self.dt
        self.cur_pos = np.array(pos)

    def rename_id(self, id):
        self.id = id

    def isActive(self):
        return self.switch

    def get_id(self):
        return self.id

    def get_pos_as_list(self):
        return self.cur_pos.tolist()

    def get_prev_pos(self):
        return self.prev_pos

    def get_data(self):
        # if this channel is note active, return None
        if not self.switch:
            return [0, 0, 0, 0]

        # if this channel specified to random, generate random data
        if self.random:
            return self.random_data()

        # ELSE: generate proper data set
        else:
            return self.generate_data()

    def circular_rep(self):
        # 'raw' euclidean distance of the position from the origin
        dist = self.cur_pos - self.origin
        norm = np.linalg.norm(dist)

        # calculate normalized radius. Normalization done by stretching the maximum value to 1.
        radius = np.sqrt(norm / self.max_norm)

        # calculate the angle from the origin
        tan = 0 if dist[0] == 0 else np.abs(np.tanh(dist[1] / dist[0]))
        return [radius, tan]

    def get_positional_data(self):
        if self.grid_string == "Circular":
            return self.circular_rep()

        # else => Origin maybe not CENTER
        # If origin is center, the normalization is just *2 for both axis
        elif self.origin_string == "Center":
            return [2 * np.abs(self.cur_pos[0] - self.origin[0]), 2 * np.abs(self.cur_pos[1] - self.origin[1])]

        # If origin is X center, Y bottom, the normalization is *2 only for X axis
        elif self.origin_string == "Center_bottom":
            return [2 * np.abs(self.cur_pos[0] - self.origin[0]), np.abs(self.cur_pos[1] - self.origin[1])]

        # else => origin is default (bottom left), no normalization required
        else:
            return self.cur_pos

    def get_velocity(self):
        # calculate pure velocity
        vel = np.linalg.norm(self.cur_pos - self.prev_pos) / self.dt
        # normalize: dividing by arbitrary number that was chosen by observations
        return vel / self.vel_normalization

    def touch_time_function(self, x):
        # sigmoid function
        if self.touch_time < 0.1:
            return 1 / (1 + np.exp((-20*x) +4))
        return 1 / (1 + np.exp((-x/2) + 4))

    def get_touch_time(self):
        return self.touch_time_function(self.touch_time)

    def generate_data(self):
        position = self.get_positional_data()
        velocity = [min(1.0, self.get_velocity())]
        touch_time = [self.get_touch_time()]
        return position + velocity + touch_time

    def random_data(self):
        mean1, sd1 = self.cur_pos[0], np.abs(self.cur_pos[1])
        mean2, sd2 = self.cur_pos[1], np.abs(self.cur_pos[0])
        x = np.random.normal(mean1, sd1)
        y = np.random.normal(mean2, sd2)

        return [np.abs(min(1.0, x)), np.abs(min(1.0, y))]

    def __repr__(self):
        return "Id :{}, Active?: {},Position: {}".format(self.id, self.switch, self.cur_pos)


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
        self.positional_clients = self.initialize_positional_clients()
        self.generated_data_clients = self.initialize_generated_data_clients_clients()

    def initialize_positional_clients(self):
        list = []
        list.append(LSLbroadcast(self.channels, self.generate_type_string()))
        return list

    def initialize_generated_data_clients_clients(self):
        list = []
        list.append(UDPclient())
        if PRINT_DATA:
            list.append(Printer())
        return list

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
        generated_data = []
        positional_data = []
        for ch in self.channels:
            positional_data += ch.get_pos_as_list()
            generated_data += ch.get_data()

        # Broadcasting the positional_data (i.e to LSL)
        for client in self.positional_clients:
            client.broadcast(positional_data)

        # Broadcasting the generated_data (i.e to MAX)
        for client in self.generated_data_clients:
            client.broadcast(generated_data)

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
                    ch.move([touch.sx, touch.sy])
                    ch.rename_id(touch.id)
                    ch.activate()
                    break

    def on_touch_move(self, touch):
        if touch.device == self.TOUCH_SCREEN:
            for ch in [*self.channels, self.waiting_ch]:
                if ch.get_id() == touch.id:
                    ch.move([touch.sx, touch.sy])
                    break

    def on_touch_up(self, touch):
        if touch.device != self.TOUCH_SCREEN:
            return
        for ch in self.channels:
            if ch.get_id() == touch.id:
                if self.waiting_ch.isActive():
                    ch.rename_id(self.waiting_ch.get_id())
                    ch.move(self.waiting_ch.get_pos_as_list())
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
