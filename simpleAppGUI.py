import time
from matplotlib import pyplot as plt
from pylsl import StreamInfo, StreamOutlet
import tkinter as tk
import pyxdf as xdf
import numpy as np
import multiprocessing as mp



def change(link):
    link['text'] = "Unlink"
    link['command'] = lambda : exit()

def push(link):
    change(link)
    demo_data_rand()

    #################################### MULTI PROCESSING SECTION #####################################

def create_workers(processes : list, args=None) -> None:
    """
    Create parallel processes
    :param processes: List of function:                                   [func1,     func2,  ...]
    :param args: List of Lists additional arguments for the function      [[*args1], [*args2],...]
    NOTE: len(args) MUST BE EQUAL to len(processes)
    """

    # Sanity check
    if not args:
        args = [[] for i in range(len(processes))]

    labeled_args = []
    # Label the stream with unique ID
    LSLstreamID = 1
    for ar in args:
        labeled_args.append([LSLstreamID, *ar])
        LSLstreamID += 1

    # More sanity check
    if len(args) != len(processes):
        raise Exception("Not enough arguments for the functions! Should be {} but {} were given".format(len(processes),
                        len(args))+"\nNote: If a function doesn't require arguments, just put (None,) as args")

    for i in range(len(processes)):
        p = mp.Process(target=processes[i], args=(*labeled_args[i],))
        p.start()

        ######################################## DEMO DATA SECTION ########################################

def demo_data_rand(id : int) -> None:
    print("worker ID: ",id)
    info = StreamInfo(name='Demo Random',source_id='myuid{}'.format(id))
    print("worker {} stream info created".format(id))
    outlet = StreamOutlet(info)
    print("worker {} outlet info created".format(id))
    while True:
        mysample = [np.random.randint(-10,20)]
        outlet.push_sample(mysample)
        time.sleep(0.01)

def demo_data_line(id : int) -> None:
    print("worker ID: ",id)
    info = StreamInfo(name='Line Random', source_id='myuid{}'.format(id))
    print("worker {} stream info created".format(id))
    outlet = StreamOutlet(info)
    print("worker {} outlet info created".format(id))
    mysample = [10]
    while True:
        outlet.push_sample(mysample)
        time.sleep(0.01)

def connect_demo_to_lsl():
    """
    Generate two demo streams : Random and Line, and connect them to LSL
    """
    workers = [demo_data_line, demo_data_rand]
    create_workers(workers)

def plot_data(filename : str) -> None:
    """
    Plot the data saved from a LSL run
    The data should be in .xdf format
    :param filename: path to the file contains the data
    """
    data, header = xdf.load_xdf(filename)

    for stream in data:
        y = stream['time_series']

        if isinstance(y, list):
            # list of strings, draw one vertical line for each marker
            for timestamp, marker in zip(stream['time_stamps'], y):
                plt.axvline(x=timestamp)
                print(f'Marker "{marker[0]}" @ {timestamp:.2f}s')
        elif isinstance(y, np.ndarray):
            # numeric data, draw as lines
            plt.plot(stream['time_stamps'], y)
        else:
            raise RuntimeError('Unknown stream format')

    plt.show()








if __name__ == "__main__":
    # master=tkinter.Tk()
    # master.title("Random")
    # master.geometry("150x150")
    #
    # link=tkinter.Button(master, text="Link")
    # link['command'] = lambda a=link : push(a)
    # link.pack()
    #
    # master.mainloop()

    connect_demo_to_lsl()

    demo_data_filename = r''
    plot_data(demo_data_filename)