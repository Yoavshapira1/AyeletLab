import pandas as pd
import numpy as np
from util import CSV_COLS_PER_TASK as head_lines
from util import CIRCLES, FREE_MOTION, TAPPER
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from os import getcwd

TAIL = 30       # Tail of the animation factor
SPEED = 0.2       # FastForWard factor
FRAME_COUNTER = 0

def extract_data(path):
    """Extract the data from a given file (as path)"""
    arr = path.split('\\')
    session = arr[-1].split('_')[0]
    col_list = head_lines[session]
    data = pd.read_csv(path, usecols=col_list)
    name, trial = data.iloc[0]['subject'].split('_')
    samples_count = len(data.index)
    time_length = data.iloc[-2]["tapNum"]
    if session in [FREE_MOTION, CIRCLES]:
        data = np.dstack((data['x_pos'].to_numpy(), data['y_pos'].to_numpy()))[0]
    else:
        data = data['natRhythmTap (in ms.)'].to_numpy()
    return data, name, trial, session, samples_count, time_length

def animate(data, name, trial, session, samples_count, time_length):
    """Animate the coordinates of a single session"""

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
        if session in [CIRCLES, FREE_MOTION]:
            if FRAME_COUNTER == 0:
                plt.pause(2)
                plt.close(fig)
            xdata.append(frame[0])
            ydata.append(frame[1])
            ln.set_data(xdata[-TAIL:], ydata[-TAIL:])
        return ln,

    ani = FuncAnimation(fig, update, frames=data, init_func=init,
                        interval=time_length / samples_count / SPEED, blit=True, repeat=False)
    plt.show()


if __name__ == "__main__":

    # put here the FULL path to the file.
    # MAKE SURE you copy the full path of the file, including the hardrive prefix.
    # ALSO make sure to maintain the format: r"PATH"
    # For the example file (Tapper > Data > Example_0 > Circles_1.csv);
    path = r"C:\Users\yoavsha\Desktop\LSL\Tapper\Data\Example_0\Circles_1.csv"

    data, name, trial, session, samples_count, time_length = extract_data(path)
    animate(data, name, trial, session, samples_count, time_length)

