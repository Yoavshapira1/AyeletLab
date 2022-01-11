import time
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
import csv

# TODO: open new directory for every subject, even with same name

TOUCH_SCREEN = "mouse"
data = []
subject_id = ""
interval = 60
dir = os.getcwd()

# read the parameters: Subject & Time
with open(dir+r'\config.txt', 'r') as con:
    subject_id = con.readline().strip()
    interval = int(con.readline().strip())

# create new directory for the subject
i = 0
while True:
    if os.path.isdir(subject_id + r"_%d" % i):
        i += 1
        sub_dir = subject_id + r"_%d" % i
    else:
        break
subject_dir = subject_id + r"_%d" % i
os.mkdir(subject_id + r"_%d" % i)


class Tapper(Widget):

    def on_touch_down(self, touch):
        if touch.device == TOUCH_SCREEN:
            # data.append([subject_id, touch.id, time.time() * 100000])
            print(touch.spos)
            print(touch.dsx, touch.dsy)

    def on_touch_move(self, touch):
        if touch.device == TOUCH_SCREEN:
            print(touch.spos)
            print(touch.dsx, touch.dsy)

    def on_touch_up(self, touch):
        if touch.device == TOUCH_SCREEN:
            print(touch.spos)
            print(touch.dsx, touch.dsy)

class MyApp(App):

    def build(self):
        Clock.schedule_once(self.close_application, interval)
        return TouchInput()

    def close_application(self, *args):
        self.toCSV()
        App.get_running_app().stop()
        Window.close()

    def toCSV(self, *args):
        global subject_id
        titles = ['subject_id', 'tapNum', 'natRhythmTap']
        file_name = dir+r'\subject_id_{}.csv'.format(subject_id)
        if os.path.isfile(file_name):
            file_name = dir+r'\subject_id_{}_2.csv'.format(subject_id)
        with open(file_name, 'w') as f:
            write = csv.writer(f)
            write.writerow(titles)
            write.writerows(data)

if __name__ == "__main__":
    MyApp().run()



