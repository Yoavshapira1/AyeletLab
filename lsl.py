import time
from random import random as rand
from pylsl import StreamInfo, StreamOutlet
import tkinter

def change(link):
    link['text'] = "Unlink"
    link['command'] = lambda : exit()

def push(link):
    change(link)
    info = StreamInfo('EXE_trial1', 'RANDOM', 1, 100, 'float32', 'myuid34234')
    outlet = StreamOutlet(info)

    while True:
        mysample = [rand()]
        outlet.push_sample(mysample)
        time.sleep(0.01)

if __name__ == "__main__":
    master=tkinter.Tk()
    master.title("Random")
    master.geometry("150x150")

    link=tkinter.Button(master, text="Link")
    link['command'] = lambda a=link : push(a)
    link.pack()

    master.mainloop()