import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from pylsl import StreamInfo, StreamOutlet
from pythonosc.udp_client import SimpleUDPClient
import numpy as np

# TODO: Option for expanding area after the touches collapse

# UDP details
IP = "127.0.0.1"
CLIENT_PORT = 2222
SERVER_PORT = 2223

########################## Developing section ###############################
# Turn this on if you want to print the data generated by th machine
PRINT_DATA = False
# Turn this on if you are currently without a touch pad, and want enable mouse touchs
MOUSE_DEV_MODE = False
######################## END developing section #############################

# Determines how many different touch detections can be realized by the MaxPatches machine as different channels
CHANNELS = 1
# Scale of the time series
TIME_SERIES_DT = 0.01

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

# don't change this:
parameters = [ORIGIN, GRID]
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
    max_area = 0.5
    min_area = 0.05
    dt = 0.01  # The delta in time which used to calculate velocity
    CH_ID = 0

    def __init__(self, origin, grid):
        # identity attributes
        TouchEvent.CH_ID += 1
        self.channel_id = TouchEvent.CH_ID
        self.id = TouchEvent.CH_ID
        self.origin = ORIGIN_dict[origin]
        self.grid = GRID_dict[grid]
        self.origin_string = origin
        self.grid_string = grid

        # data-generating related
        self.touch_time = 0
        self.max_norm = np.linalg.norm(np.array([1, 1]) - self.origin)
        self.reduce_time_threshold = self.max_norm / 300  # ||pos - prev_pos|| > threshold => reduce time_touch
        self.vel_normalization = 5          # An arbitrary number - was chosen by observations
        self.start_pos = np.array([0.0, 0.0])
        self.mode = 0
        # initialize the values to zero
        self.deactivate()

    def rename_id(self, id):
        self.id = id

    def isActive(self):
        return self.switch

    def get_id(self):
        return self.id

    def get_channel_id(self):
        return self.channel_id

    def get_pos_as_list(self):
        return self.cur_pos.tolist()

    def get_prev_pos(self):
        return self.prev_pos

    def get_start_time(self):
        return self.time_start

    def get_group(self):
        return self.group

    def remove_from_group(self, groupy):
        self.group.remove(groupy)

    def activate(self):
        """When a touch event is begin"""
        self.prev_pos = self.cur_pos
        self.start_pos = self.cur_pos
        self.time_start = time.time()
        self.switch = True

    def deactivate(self):
        """After a touch event is leaving the screen"""
        self.cur_pos = np.array([0.0, 0.0])
        self.prev_pos = np.array([0.0, 0.0])    # The previous position is been updated every dt
        self.prev_pos_time = time.time()
        if self.touch_time < 0.04:
            self.next_mode()
        self.touch_time = 0
        self.switch = False
        self.group = []

    def next_mode(self):
        """For a very short touch"""
        self.mode += 1

    def prev_mode(self):
        """For a very short double-touch"""
        self.mode = max(self.mode - 1, 0)

    def move(self, pos):
        """In every movement, and only if move"""
        # change previous position only if dt time has passed
        if time.time() - self.prev_pos_time > self.dt:
            # reduce the time touch value if position is changed a lot
            ds = np.linalg.norm(self.cur_pos - self.prev_pos)
            if ds > self.reduce_time_threshold:
                self.touch_time *= 0.1       # ds < 1 so results in reducing value
            self.prev_pos = self.cur_pos
            self.prev_pos_time = time.time()
            self.touch_time += self.dt
        self.cur_pos = np.array(pos)

    def add_to_group(self, touch):
        """Add a touch event to the group of this one.
        NOTICE: The touch event is a Kivy based! follows Kivy's "TouchInput" API"""
        self.group.append(touch)

    def positional_circular_rep(self) -> list:
        """Generate the circular positional attributes"""
        # 'raw' euclidean distance of the position from the origin
        dist = self.cur_pos - self.origin
        norm = np.linalg.norm(dist)

        # calculate normalized radius. Normalization done by stretching the maximum value to 1.
        radius = np.sqrt(norm / self.max_norm)

        # calculate the angle from the origin
        tan = 0 if dist[0] == 0 else np.abs(np.tanh(dist[1] / dist[0]))
        return [radius, tan]

    def get_positional_data(self):
        """Generate the positional attributes"""
        if self.grid_string == "Circular":
            return self.positional_circular_rep()

        # else => Origin maybe not CENTER
        # If origin is center, the normalization is just *2 for both axis
        elif self.origin_string == "Center":
            return [2 * np.abs(self.cur_pos[0] - self.origin[0]), 2 * np.abs(self.cur_pos[1] - self.origin[1])]

        # If origin is X center, Y bottom, the normalization is *2 only for X axis
        elif self.origin_string == "Center_bottom":
            return [2 * np.abs(self.cur_pos[0] - self.origin[0]), np.abs(self.cur_pos[1] - self.origin[1])]

        # else => origin is default (bottom left), no normalization required
        else:
            return self.get_pos_as_list()

    def get_velocity(self):
        """Calculate velocity in respect to time interval of self.dt"""
        # calculate pure velocity
        vel = np.linalg.norm(self.cur_pos - self.prev_pos) / self.dt
        # normalize: dividing by arbitrary number that was chosen by observations
        return vel / self.vel_normalization

    def touch_time_function(self, x):
        # sigmoid function
        if self.touch_time < 0.07:
            return 1 / (1 + np.exp((-20*x) +4))
        return 1 / (1 + np.exp(-x + 4))

    def get_touch_time(self):
        """Calculate the continuously touching time"""
        return self.touch_time_function(self.touch_time)

    def get_area(self):
        """Calculate the density of the touch's group. The density defined as the AREA between the groupy.
        Hence if the group is either empty or contain 1 touch, this value equals to 0"""
        if len(self.group) > 0:
            area = np.linalg.norm(self.cur_pos - self.group[0].spos)
            area = (area - self.min_area) / (self.max_area - self.min_area)
            return max(0.0, min(area, 1.0))
        else:
            return 0.0

    def get_qualitiative_data(self):
        """Generate the data sent to UDP. The data is a list of concatenated values:
        [start_pos_x, start_pos_y, pos_x, pos_y, velocity, touch_time, mode, density]"""
        # if this channel is note active
        start_pos = [self.start_pos[0], self.start_pos[1]]
        if not self.switch:
            return start_pos + [0.0] * 6

        position = self.get_positional_data()
        velocity = [min(1.0, self.get_velocity())]
        touch_time = [self.get_touch_time()]
        mode = [self.mode]
        area = [self.get_area()]
        return start_pos + position + velocity + touch_time + mode + area

    def __repr__(self):
        return "Id :{}, Active?: {},Position: {}".format(self.id, self.switch, self.cur_pos)


class UDPclient:
    """
    Object represents the connection to the UDP, which holds for the communication with Max8.
    """

    def __init__(self):
        self.client = SimpleUDPClient(IP, CLIENT_PORT)

    def broadcast(self, data):
        self.client.send_message('/channel1', data[0][1])
        # for ch in data:
        #     self.client.send_message(ch[0], ch[1])

class Printer:
    """
    Broadcaster to the screen
    """

    def broadcast(self, data):
        for ch in data:
            print(ch[0], ch[1])

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
               ", " + "Grid: " + parameters[1]

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
            generated_data.append(["channel%d" % ch.get_channel_id(), ch.get_qualitiative_data()])

        # Broadcasting the positional_data (i.e to LSL)
        for client in self.positional_clients:
            client.broadcast(positional_data)

        # Broadcasting the generated_data (i.e to MAX)
        for client in self.generated_data_clients:
            client.broadcast(generated_data)

class TouchInput(Widget):

    def __init__(self, channels, mouse_mode, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.waiting_ch = TouchEvent(*parameters)
        self.touch_mode = "mouse" if mouse_mode else "wm_touch"

    def on_touch_down(self, touch):
        # If not touch mode type, do nothing
        if touch.device == self.touch_mode:
            for ch in [*self.channels, self.waiting_ch]:
                # If there is no active touch - create one
                if not ch.isActive():
                    if touch.is_double_tap:
                        ch.prev_mode()
                    else:
                        ch.move([touch.sx, touch.sy])
                        ch.rename_id(touch.id)
                        ch.activate()
                    break
                # If there is an active channel, and the current touch occurred immediately after it - Add to group
                if time.time() - ch.get_start_time() < 0.3:
                    ch.add_to_group(touch)
                    break

    def on_touch_move(self, touch):
        if touch.device == self.touch_mode:
            for ch in [*self.channels, self.waiting_ch]:
                if ch.get_id() == touch.id:
                    ch.move([touch.sx, touch.sy])
                    break

    def on_touch_up(self, touch):
        if touch.device != self.touch_mode:
            return
        for ch in self.channels:
            # Case: The touch up refers to an active channel
            if touch.id == ch.get_id():
                # Case: The channel have an active group => change the channel to one of the groupies
                if len(ch.get_group()) > 0:
                    new_touch = ch.get_group()[0]
                    ch.move([new_touch.sx, new_touch.sy])
                    ch.rename_id(new_touch.id)
                    ch.remove_from_group(new_touch)
                    break
                # Case: Waiting channel is active => Replace channels
                if self.waiting_ch.isActive():
                    ch.rename_id(self.waiting_ch.get_id())
                    ch.move(self.waiting_ch.get_pos_as_list())
                    ch.activate()
                    self.waiting_ch.deactivate()
                # else => deactivate
                else:
                    ch.deactivate()
                break
            # Case: the touch up related to one of the channel's groupies (in this case
            # the channels must be activated) => remove it from the group
            if touch in ch.get_group():
                ch.remove_from_group(touch)
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
        Clock.schedule_interval(self.broadcaster.broadcast, TIME_SERIES_DT)
        return TouchInput(self.channels, mouse_mode=MOUSE_DEV_MODE)

if __name__ == "__main__":

    # Avoiding the user from accidentally close the app
    # App closes ONLY if <escape> is pressed
    # Window.fullscreen = True
    # Window.borderless = True
    # Window.maximize()
    Window.exit_on_escape = True

    # Run the app
    MyApp().run()