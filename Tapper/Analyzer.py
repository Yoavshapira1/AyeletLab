import pandas as pd
import numpy as np
import scipy.stats
from util import CSV_COLS_PER_TASK as head_lines
from util import CIRCLES, FREE_MOTION, TAPPER
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation
from scipy import signal
from scipy.ndimage import gaussian_filter1d
from sklearn.cluster import KMeans

# TODO: create intervals files: both for whole circle and for entire peaks set

################# animation parameters ####################
ANIMATION_TAIL = 90         # Tail of the animation factor
ANIMATION_SPEED = 0.2       # FastForWard factor
FRAME_COUNTER = 0           # don't change this

############### pre-process parameters ####################
TRIM_SEC = 2               # time of the beginning of the trial to be cut, in sec.
CHUNK_SAMPLES = 1          # bulking factor of the samples

############## velocity process parameters ################
MULTIPY_FACTOR = 1000      # velocity values are to be multiplied by this value to get human-realizable values

# The next variables are for the filter size of the velocity vector.
# Define the points on the circle where the velocity on the axis decreases as 'intentionally slowing' points.
# The faster the movement --> The less 'noisy' points (which are not intentionally slowing) on the velocity vector
# Therefor, The slower the movement --> The bigger filter size required to detect the intentionally slowing and
# extract the peaks for the intervals analyzing.
# Here, an arbitrary mean (of velocity) chosen from observations, and this value requires minial filtering.
# Every 0.1 below this value requires more 1 filter size
VELOCITY_FILTER_SIZE = 3
DEFAULT_VEL_MEAN = 1.3

INTERVALS_BINS = 20            # bins for the intervals histogram
OUTLIERS_TOL = 1               # tolerance for outliers. POSITIVE INTEGER
PEAKS_SGN = -1                 # sign of the peaks: 1 for Max and -1 for Min
COLORS = {'vel' : 'C0', 'vel_smooth' : 'C1', 'vel_filtered' : 'C2'}

# TODO : fix data trimming without time_length signature
# TODO: ignore the file if the data is trimmed in the end al lot


def extract_data(path):
    """Extract the data from a given file (as path)"""
    arr = path.split('\\')
    session = arr[-1].split('_')[0]
    screen_type = "small" if arr[-1].split('_')[1].split('.')[0]=='1' else "big"
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
        "screen_type" : screen_type,
        "n_samples" : len(data),
        "number" : num,
        "name" : name,
        "trial" : trial,
        "time_length" : time_length - TRIM_SEC,
        "time_prespective" : time_perspective - TRIM_SEC
            }

    return dict

def normalize_arr(arr):
    return (arr - np.min(arr)) / (np.max(arr) - np.min(arr))

def animate_free_movement(data_dict):
    """Animate the coordinates of a single session"""

    name = data_dict['name']
    trial = data_dict['trial']
    session = data_dict['session']
    n_samples = data_dict['n_samples']
    time_length = data_dict['time_length']
    vel = normalize_arr(data_dict['vel'])


    if session not in [FREE_MOTION, CIRCLES]:
        raise Exception("Function 'animate_free_movement' can only work with data from sessions 'FREE_MOTION' or 'CIRCLES'")

    data = data_dict['npdata'][1:]

    fig, ax = plt.subplots(figsize=(16,9))
    ax.set_title("subject: %s, %s session number %d" % (name, session, int(trial)+1), fontdict=None, loc='center', pad=None)
    xdata, ydata, col = [], [], []
    ln, = plt.plot([], [], 'o')
    global FRAME_COUNTER
    FRAME_COUNTER = len(data)

    viridis = cm.get_cmap('viridis', len(vel))
    cmap = viridis(vel, len(vel))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    def init():
        return ln,

    def update(frame):
        global FRAME_COUNTER
        FRAME_COUNTER -= 1
        if FRAME_COUNTER == 0:
            plt.pause(1)
            plt.close(fig)
        xdata.append(frame[0])
        ydata.append(frame[1])
        col.append('%f' % vel[-FRAME_COUNTER])
        ln.set_data(xdata[-ANIMATION_TAIL:], ydata[-ANIMATION_TAIL:])
        ln.set_color(cmap[-FRAME_COUNTER])
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

def plot_velocity_vector(data, ax, fil_size=VELOCITY_FILTER_SIZE, smooth=False, filtered=False):
    time_stamp = data['data'].loc[1:]['time_stamp (in ms.)']
    if smooth:
        vec = data['vel_smooth']
        c = COLORS['vel_smooth']
    elif filtered:
        vec = data['vel_filtered']
        c = COLORS['vel_filtered']
        ax.plot([], [], ' ', label="filter size: %d" % fil_size)
    else:
        vec = data['vel']
        ax.plot([], [], ' ', label=r'$\mu$: %.2f.  $\sigma^2$: %.2f' % (np.mean(vec), np.var(vec)))
        c = COLORS['vel']

    ax.legend(loc='upper left', prop={'size': 8})
    ax.set_yticks([])
    ax.set(ylabel="Vel.")
    ax.plot(time_stamp, vec, c=c)

def plot_fft(x_dft, y_dft, ax):
    ax.set(xlabel="Freq.", ylabel="Amp.")
    ax.plot(x_dft, y_dft)

def separate_high_peaks(data):
    center_y = np.mean(data['npdata'][:, 1])

    # for every peak P, check if the next points in data are in descending order in the y axis
    # check out half of the points between two peaks
    # if YES: insure that P_y is > center_y
    res = []
    for i in range(len(data['peaks'][:-1])):
        p_cur = data['peaks'][i]
        p_next = data['peaks'][i+1]
        if data['npdata'][p_cur][1] > np.average(data['npdata'][p_cur:p_next][:, 1]) and data['npdata'][p_cur][1] > center_y:
            res.append(p_cur)
    p_last = data['peaks'][-1]
    if data['npdata'][p_last][1] > np.average(data['npdata'][p_last:][:, 1]):
        res.append(p_last)
    data['high_peaks'] = np.array(res)
    data['not_high_peaks'] = np.setdiff1d(data['peaks'], data['high_peaks'])

def plot_peaks(data, ax):
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set(ylabel="vel.")
    ax.plot(data['vel'], alpha=1)
    for x in data['high_peaks']:
        ax.axvline(x, color='red', linestyle='--', linewidth=0.8)
    for x in data['not_high_peaks']:
        ax.axvline(x, color='Orange', linestyle='--', linewidth=0.8)
    ax.scatter(data['not_high_peaks'], data['vel'][data['not_high_peaks']], marker="^", color='Orange', zorder=2, linewidth=0.3, edgecolors='black', s=20)
    ax.scatter(data['high_peaks'], data['vel'][data['high_peaks']], marker='o', color='red', zorder=2, linewidth=0.3, edgecolors='black', s=20)

def plot_interval_hist(data, ax):
    ax.set_yticks([])
    x = data['intervals']
    mu, sd = np.mean(x), np.sqrt(np.var(x))
    x = x[x >= np.abs(mu - (OUTLIERS_TOL * sd))]        # clean outliers
    density, bins, patches = ax.hist(x, density=True, bins=INTERVALS_BINS, edgecolor='black', linewidth=1., color='Orange')

    mn, mx = ax.set_xlim()
    ax.set_xlim(mn, mx)
    # kde_xs = np.linspace(mn, mx, 300)
    # kde = scipy.stats.gaussian_kde(x)
    # pdf = kde.pdf(kde_xs)
    # ax.plot(kde_xs, pdf, c='r', alpha=0.5)
    ax.plot([], [], ' ', label=r'$\mu$: %.0f.  $\sigma$: %.0f' % (np.mean(x), np.sqrt(np.var(x))))
    ax.legend(loc='upper left', prop={'size': 8})
    ax.set(xlabel="ms.")

def plot_smooth_vec(data, ax):
    mean = np.mean(data['vel'])
    filter_size = int(VELOCITY_FILTER_SIZE + (0 if mean > DEFAULT_VEL_MEAN else 14 * np.abs(mean - DEFAULT_VEL_MEAN)))
    data['vel_filtered'] = gaussian_filter1d(data['vel'], filter_size)
    plot_velocity_vector(data, ax[1], fil_size=filter_size, filtered=True)

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
    ax_arr[0].set_title("SUBJECT: %s, TASK: %s, SCREEN SIZE: %s" % (data['name'], data['session'], data['screen_type']))

    # analyze motion data
    if data['session'] in [FREE_MOTION, CIRCLES]:
        data['data'] = preprocess_motion(data['data'])

        # generate positional data as numpy array
        data['npdata'] = np.array([data['data']['x_pos'], data['data']['y_pos']]).T
        # generate velocity vector
        data['vel'] = get_velocity_vector(data)
        plot_velocity_vector(data, ax_arr[0])
        # Smooth the vector with Gaussian Filter
        plot_smooth_vec(data, ax_arr)

        # Find the peaks (minima) of the velocity vector
        data['peaks'], _ = signal.find_peaks(PEAKS_SGN * (data['vel_filtered']), height=-np.inf)
        # data['peaks_time_stamps'] = data['data']['time_stamp (in ms.)'] \
        #     .reset_index().loc[data['peaks']].rename(columns={"time_stamp (in ms.)": "natRhythmTap (in ms.)"})
        # data['peaks_time_stamps'].to_csv(path[:-4] + "_peaks_int.csv")
        separate_high_peaks(data)
        plot_peaks(data, ax_arr[2])

        p = (data['data']['time_stamp (in ms.)'].reset_index(drop=True))[data['high_peaks']]
        data['intervals'] = p[1:].copy().reset_index(drop=True).subtract(p[:-1].copy().reset_index(drop=True))
        plot_interval_hist(data, ax_arr[3])

        if animate:
            animate_free_movement(data)

    return data

def init_axis(ax, title):
    ax.annotate(title, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - 5, 0),
                       xycoords=ax.yaxis.label, textcoords='offset points',
                       size='large', ha='right', va='center')

def analyze_velocity_peaks(files, animate=False):
    data = []
    axis_slots = 4
    map = False if len(files) > 1 else True
    if not map:
        fig, axs = plt.subplots(axis_slots, len(files))
    else:
        fig, axs = plt.subplots(axis_slots, 2)

    # plot the velocity, filtered vel., minimum velocity peaks, and histogram of the intervals
    init_axis(axs[0][0], "Velocity:")
    init_axis(axs[1][0], "Smooth:")
    init_axis(axs[2][0], "Peaks:")
    init_axis(axs[3][0], "Intervals hist.:")
    for file, ax in zip(files, axs.T):
        data.append(plot_analyze(file, ax, animate))

    if map:
        data = data[0]
        # plot the velocity peaks of the data on the movements shape. not that peaks are MINIMA points
        gs = axs[1, 0].get_gridspec()
        # remove the underlying axes
        for ax in axs[0:, -1]:
            ax.remove()
        axbig = fig.add_subplot(gs[0:, -1])
        axbig.set_xlim(0, 1)
        axbig.set_ylim(-1.2, 2.2)
        axbig.get_xaxis().set_visible(False)
        axbig.get_yaxis().set_visible(False)
        axbig.set_title("Minimal velocity points (including outliers) along the move")
        axbig.scatter(data['npdata'][:,0], data['npdata'][:,1], alpha=0.8)
        axbig.scatter(data['npdata'][:,0][data['not_high_peaks']], data['npdata'][:,1][data['not_high_peaks']], marker="^", color='Orange', zorder=2, edgecolors='black', linewidths=1.)
        axbig.scatter(data['npdata'][:,0][data['high_peaks']], data['npdata'][:,1][data['high_peaks']], marker="o", color='r', zorder=2, edgecolors='black', linewidths=1.)

    plt.show()

if __name__ == "__main__":
    base = r'C:\Users\yoavsha\Desktop\LSL\Tapper\Data'
    motion_small_screen = r'\Motion_1.csv'
    motion_big_screen = r'\Motion_2.csv'
    circles_small_screen = r'\Circles_1.csv'
    circles_big_screen = r'\Circles_2.csv'

    subj = r'\s05_nt_0'

    two_sec_circles = base + r'\yoav_120sec_round_0\Circles_1.csv'
    f1 = base + subj + circles_small_screen
    f2 = base + subj + circles_big_screen

    files = [f1,f2]

    analyze_velocity_peaks(files, animate=False)






