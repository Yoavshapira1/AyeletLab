import pandas as pd
import numpy as np
from util import CSV_COLS_PER_TASK as head_lines
from util import CIRCLES, FREE_MOTION, TAPPER
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from os import getcwd

ANIMATION_TAIL = 30         # Tail of the animation factor
ANIMATION_SPEED = 0.2       # FastForWard factor
FRAME_COUNTER = 0           # don't change this

TRIM_CONST = 2               # time of the beginning of the trial to be cut, in sec.


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
    n_samples = len(data.index)
    time_length = data.iloc[-2]["tapNum"]
    if session in [FREE_MOTION, CIRCLES]:
        data = np.dstack((data['x_pos'].to_numpy(), data['y_pos'].to_numpy()))[0]
    else:
        data = data['natRhythmTap (in ms.)'].to_numpy()
    start_trim = int(TRIM_CONST / time_length * n_samples)
    return data[start_trim:], name, trial, session, n_samples - start_trim, time_length - TRIM_CONST


def animate_free_movement(data, name, trial, session, n_samples, time_length):
    """Animate the coordinates of a single session"""

    if session not in [FREE_MOTION, CIRCLES]:
        raise Exception("Function 'animate_free_movement' can only work with data from sessions 'FREE_MOTION' or 'CIRCLES'")

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


def get_velocity_vector(data, session):
    if session not in [FREE_MOTION, CIRCLES]:
        raise Exception("Function 'get_velocity_vector' can only work with data from sessions 'FREE_MOTION' or 'CIRCLES'")

    dt = time_length / n_samples
    dist = np.linalg.norm(data[1:] - data[:-1], axis=1)
    return dist / dt


def plot(data, title, ytitle, xtitle):
    plt.clf()
    plt.title(title)
    plt.plot(data)
    plt.show()


if __name__ == "__main__":

    # put here the FULL path to the file.
    # MAKE SURE you copy the full path of the file, including the hardrive prefix.
    # ALSO make sure to maintain the format: r"PATH"
    # For the example file (Tapper > Data > Example_0 > Circles_1.csv);
    path = r"C:\Users\yoavsha\Desktop\LSL\Tapper\Data\Const_Vel_0\Motion_line_1.csv"

    data, name, trial, session, n_samples, time_length = extract_data(path)
    animate_free_movement(data, name, trial, session, n_samples, time_length)
    plot(get_velocity_vector(data, session), title="Velocity in time", xtitle="Velocity", ytitle="Samples")



