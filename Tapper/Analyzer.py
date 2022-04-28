import pandas as pd
import numpy as np
from util import CSV_COLS_PER_TASK as head_lines
from util import CIRCLES, FREE_MOTION, TAPPER
from matplotlib import use
use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import savgol_filter

ANIMATION_TAIL = 30         # Tail of the animation factor
ANIMATION_SPEED = 0.2       # FastForWard factor
FRAME_COUNTER = 0           # don't change this

TRIM_SEC = 2               # time of the beginning of the trial to be cut, in sec.
CHUNK_SAMPLES = 5


def extract_data(path):
    """Extract the data from a given file (as path)
    ":return ndarray contains the data. array shape changes due to the session:
             For Free Motion/Circles sessions: (n_samples, 2) holds the (x,y) position of each sample
             For Tapping:                      (n_samples, )  holds the timing of each sample
     """
    arr = path.split('\\')
    session = arr[-1].split('_')[0]
    col_list = head_lines[session]
    data = pd.read_csv(path, usecols=col_list)
    name, trial = data.iloc[0]['subject'].split('_')[0], data.iloc[0]['subject'].split('_')[-1]
    time_length = data.iloc[-2]["tapNum"]
    time_perspective = data.iloc[-1]["tapNum"]

    # trim the beginning of the data and normalize the time stamp and the sample count accordingly
    data = data.iloc[int(TRIM_SEC * len(data) / time_length):].reset_index()
    data['time_stamp (in ms.)'] = data['time_stamp (in ms.)'] - data['time_stamp (in ms.)'][0]

    # old index and name of subject are not necessary anymore
    data = data.drop(['subject', 'index'], axis=1)[:-2]

    dict = {
        "data": data,
        "session" : session,
        "n_samples" : len(data),
        "name" : name,
        "trial" : trial,
        "time_length" : time_length - TRIM_SEC,
        "time_prespective" : time_perspective - TRIM_SEC
            }

    return dict


def animate_free_movement(data_dict):
    """Animate the coordinates of a single session"""

    name = data_dict['name']
    trial = data_dict['trial']
    session = data_dict['session']
    n_samples = data_dict['n_samples']
    time_length = data_dict['time_length']

    if session not in [FREE_MOTION, CIRCLES]:
        raise Exception("Function 'animate_free_movement' can only work with data from sessions 'FREE_MOTION' or 'CIRCLES'")

    data = np.array([data_dict['data']['x_pos'], data_dict['data']['y_pos']]).T

    fig, ax = plt.subplots(figsize=(16,9))
    ax.set_title("subject: %s, %s session number %d" % (name, session, int(trial)+1), fontdict=None, loc='center', pad=None)
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'ro')
    global FRAME_COUNTER
    FRAME_COUNTER = len(data)

    def init():
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        return ln,

    def update(frame):
        global FRAME_COUNTER
        FRAME_COUNTER -= 1
        if FRAME_COUNTER == 0:
            plt.pause(1)
            plt.close(fig)
        xdata.append(frame[0])
        ydata.append(frame[1])
        ln.set_data(xdata[-ANIMATION_TAIL:], ydata[-ANIMATION_TAIL:])
        return ln,

    ani = FuncAnimation(fig, update, frames=data, init_func=init,
                        interval=time_length / n_samples / ANIMATION_SPEED, blit=True, repeat=False)
    plt.show()


def preprocess_motion(data):

    # Chunks the data into bulks of size of CHUNK_SAMPLES
    data = data.iloc[::CHUNK_SAMPLES, :]

    # replaces -1 to nan
    data.replace(-1, np.nan, inplace=True)

    # interpolate to fill the nan values
    data['x_pos'].interpolate(method="linear", inplace=True)
    data['y_pos'].interpolate(method="linear", inplace=True)

    return data

def get_velocity_vector(data):
    dt = np.array(data['data']['time_stamp (in ms.)'][1:]) - np.array(data['data']['time_stamp (in ms.)'][:-1])
    dist = np.linalg.norm(data['npdata'][1:] - data['npdata'][:-1], axis=1)
    return dist / dt


def get_fft(one_D_data):

    # calculate fft shifted to the center
    yfft = np.fft.fft(one_D_data)
    yfft = np.fft.fftshift(yfft)

    # calculate the frequencies, shifted to the center
    xfft = np.fft.fftfreq(len(one_D_data))
    xfft = np.fft.fftshift(xfft)

    # applying a high pass filter to remove 0-frequency artefact
    mask = np.ones(len(xfft))
    mask[np.where(xfft == 0)] = 0

    return xfft*mask, yfft*mask


def plot_velocity_vector(vel, time_stamp, title="Velocity in time", y_title="Vel.", x_title="ms."):
    plt.clf()
    plt.title(title)
    plt.ylabel(y_title)
    plt.xlabel(x_title)
    plt.plot(time_stamp, vel)
    plt.plot([], [], ' ', label="Maximum difference: %.4f" % (np.max(vel) - np.min(vel)))
    plt.legend()
    plt.show()


def plot_fft(x_dft, y_dft,  title="DFT of the velocity", y_title="Amp.", x_title="Freq."):
    plt.clf()
    plt.title(title)
    plt.ylabel(y_title)
    plt.xlabel(x_title)
    plt.plot(x_dft, y_dft)
    plt.legend()
    plt.show()

if __name__ == "__main__":

    path = r"R:\Experiments\resoFreq_vis_BEH\Glass_Tapper\Data_r\s07_nd_0\Motion_1.csv"

    # Extract the data into a dictionary structure with the next keys:
    #   session          : <String>; one of: "FREE MOTION", "CIRCLES", "TAPPER"
    #   data             : <pd.DataFrame>; columns corresponding to CSV_COLS_PER_TASK(session)
    #   n_samples        : <Integer>; number of samples in the data
    #   name             : <String>; name of the subject
    #   trial            : <Integer>; number of the trial
    #   time_length      : <Integer>; total time the trial took, in sec.
    #   time_perspective : <Integer>; time the subject thought that passed, in sec.
    data = extract_data(path)

    # animate_free_movement(data)

    # analyze motion data
    if data['session'] in [FREE_MOTION, CIRCLES]:

        # preprocess: delete -1 and NaN
        data['data'] = preprocess_motion(data['data'])

        # generate positional data as numpy array
        data['npdata'] = np.array([data['data']['x_pos'], data['data']['y_pos']]).T

        # generate velocity vector
        data['vel'] = get_velocity_vector(data)

        plot_velocity_vector(data['vel'], data['data'].loc[1:]['time_stamp (in ms.)'])

        # Smooth the signal. window size is currently 1 second
        win_size = int(len(data['vel']) / data['time_length']) if int(len(data['vel']) / data['time_length']) % 2 == 1\
                    else int(len(data['vel']) / data['time_length']) + 1
        data['vel_smooth'] = savgol_filter(data['vel'], win_size, 3)
        plot_velocity_vector(data['vel_smooth'], data['data'].loc[1:]['time_stamp (in ms.)'], title="Smooth velocity vector")

        # Calculate dft on the smooth velocity vector and plot it
        data_dft_x, data_dft_y = get_fft(data['vel_smooth'])
        plot_fft(data_dft_x, data_dft_y)



