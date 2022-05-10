import pandas as pd
import numpy as np
import scipy.stats

from util import CSV_COLS_PER_TASK as head_lines
from util import CIRCLES, FREE_MOTION, TAPPER
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy import signal
from scipy.ndimage import gaussian_filter1d

################# animation parameters ####################
ANIMATION_TAIL = 30         # Tail of the animation factor
ANIMATION_SPEED = 0.2       # FastForWard factor
FRAME_COUNTER = 0           # don't change this

############### pre-process parameters ####################
TRIM_SEC = 2               # time of the beginning of the trial to be cut, in sec.
CHUNK_SAMPLES = 1          # bulking factor of the samples

############## velocity process parameters ################
MULTIPY_FACTOR = 1000      # velocity values are to be multiplied by this value to get realizable values
VELOCITY_FILTER_SIZE = 3   # gaussian filtering factor
INTERVALS_BINS = 20        # bins for the intervals histogram
COLORS = {'vel' : 'C0', 'vel_smooth' : 'C1', 'vel_filtered' : 'C2'}

# TODO : fix data trimming without time_length signature
# TODO: ignore the file if the data is trimmed in the end al lot


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
    trial = data.iloc[0]['subject'].split('_')[-1]
    name = data.iloc[0]['subject'].split('_')[-2]
    num = data.iloc[0]['subject'].split('_')[0]
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
        "number" : num,
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
    return dist / dt * MULTIPY_FACTOR


def get_fft(one_d_data, bp_width=None):

    # Band pass factor; percentages of frequencies to trim from high and low areas
    bp_width = 33

    fft_amp = np.fft.fft(one_d_data)
    np.fft.fftshift(fft_amp)
    fft_freq = np.fft.fftfreq(len(one_d_data))
    np.fft.fftshift(fft_freq)

    mask = np.ones(len(fft_freq))
    mask[fft_freq==0] = 0
    if bp_width is not None:
        mask[(len(fft_freq)*bp_width//100):] = 0
        mask[-(len(fft_freq)*bp_width//100):] = 0

    # TODO: postprocess for FFT:
    # BAND PASS to exclude the robust freq, and the very high ones
    # AVG: average the frequencies
    # COMPARE to tapping results

    filtered_signal = np.fft.ifft(fft_amp * mask)

    return fft_freq*mask, np.abs(fft_amp*mask), filtered_signal

def plot_velocity_vector(data, ax, smooth=False, filtered=False):
    time_stamp = data['data'].loc[1:]['time_stamp (in ms.)']
    if smooth:
        vec = data['vel_smooth']
        c = COLORS['vel_smooth']
    elif filtered:
        vec = data['vel_filtered']
        c = COLORS['vel_filtered']
    else:
        vec = data['vel']
        ax.plot([], [], ' ', label=r'$\mu$: %.2f.  $\sigma^2$: %.2f' % (np.mean(vec), np.var(vec)))
        ax.legend()
        c = COLORS['vel']

    ax.set_yticks([])
    ax.set(xlabel="ms.", ylabel="Vel.")
    ax.plot(time_stamp, vec, c=c)

def plot_fft(x_dft, y_dft, ax):
    ax.set(xlabel="Freq.", ylabel="Amp.")
    ax.plot(x_dft, y_dft)

def plot_peaks(data, ax):
    ax.set_yticks([])
    ax.set(xlabel="ms.", ylabel="vel.")
    ax.plot(data['vel'])
    ax.plot(data['peaks'], data['vel'][data['peaks']], "x")

def plot_interval_hist(data, ax):
    ax.set_yticks([])
    x = data['intervals']
    ax.hist(x, density=True, bins=INTERVALS_BINS)
    mn, mx = ax.set_xlim()
    ax.set_xlim(mn, mx)
    kde_xs = np.linspace(mn, mx, 300)
    kde = scipy.stats.gaussian_kde(x)
    pdf = kde.pdf(kde_xs)
    ax.plot(kde_xs, pdf)
    ax.plot([], [], ' ', label=r'$\mu$: %.0f.  $\sigma^2$: %.0f' % (np.mean(x), np.var(x)))
    ax.legend(loc='upper left', prop={'size': 8})
    ax.set(xlabel="ms.")

def plot_analyze(path, ax_arr, animate=False):

    # Extract the data into a dictionary structure with the next keys:
    #   session          : <String>; one of: "FREE MOTION", "CIRCLES", "TAPPER"
    #   data             : <pd.DataFrame>; columns corresponding to CSV_COLS_PER_TASK(session)
    #   n_samples        : <String>; integer of number of samples in the data
    #   name             : <String>; name of the subject
    #   number           : <String>; integer of number of subject
    #   trial            : <String>; integer of number of the trial
    #   time_length      : <String>; integer of total time the trial took, in sec.
    #   time_perspective : <String>; integer of time the subject thought that passed, in sec.
    data = extract_data(path)

    ax_arr[0].set_title("subject: %s, task: %s, trial: %s" % (data['name'], data['session'], data['trial']))

    if animate:
        animate_free_movement(data)

    # analyze motion data
    if data['session'] in [FREE_MOTION, CIRCLES]:
        data['data'] = preprocess_motion(data['data'])


        # generate positional data as numpy array
        data['npdata'] = np.array([data['data']['x_pos'], data['data']['y_pos']]).T
        # generate velocity vector
        data['vel'] = get_velocity_vector(data)

        plot_velocity_vector(data, ax_arr[0])


        # Smooth the vector with Gaussian Filter
        data['vel_filtered'] = gaussian_filter1d(data['vel'], VELOCITY_FILTER_SIZE)
        plot_velocity_vector(data, ax_arr[1], filtered=True)

        # Find the peaks (minima) of the velocity vector
        data['peaks'], _ = signal.find_peaks(-(data['vel_filtered']), height=-np.inf)
        plot_peaks(data, ax_arr[2])
        ### Save the peaks time_stamp as a .csv file for the Tapping Interval Analysis
        # data['peaks_time_stamps'] = data['data']['time_stamp (in ms.)']\
        # .reset_index().loc[data['peaks']].rename(columns = {"time_stamp (in ms.)" : "natRhythmTap (in ms.)"})
        # data['peaks_time_stamps'].to_csv(path[:-4] + "_peaks_int.csv")

        p = (data['data']['time_stamp (in ms.)'].reset_index(drop=True))[data['peaks']]
        data['intervals'] = p[1:].copy().reset_index(drop=True).subtract(p[:-1].copy().reset_index(drop=True))
        plot_interval_hist(data, ax_arr[3])

def init_axis(ax, title):
    ax.annotate(title, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - 5, 0),
                       xycoords=ax.yaxis.label, textcoords='offset points',
                       size='large', ha='right', va='center')

def analyze_velocity(files):
    axis_slots = 4
    fig, axs = plt.subplots(axis_slots, len(files))

    init_axis(axs[0][0], "Velocity:")
    init_axis(axs[1][0], "Smooth:")
    init_axis(axs[2][0], "Peaks:")
    init_axis(axs[3][0], "Intervals hist.:")

    for file, ax in zip(files, axs.T):
        plot_analyze(file, ax)

    plt.show()

if __name__ == "__main__":
    base = r'C:\Users\Dell\PycharmProjects\AyeletLab\Tapper\Data'

    subj1 = r'\s02_lg_0'
    subj2 = r'\s07_nd_0'

    M1 = r'\Motion_1'
    M2 = r'\Motion_2'
    C1 = r'\Circles_1'
    C2 = r'\Circles_2'

    f1 = base + subj1 + M1 + r".csv"
    f2 = base + subj1 + C2 + r".csv"
    f3 = base + subj2 + M1 + r".csv"
    f4 = base + subj2 + C2 + r".csv"
    files = [f1, f2, f3, f4]

    analyze_velocity(files)






