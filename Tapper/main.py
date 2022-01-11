import time
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
import csv

TOUCH_SCREEN = "wm_touch"
data = []
subject_id = ""
interval = 60
# dir = os.path.abspath(os.getcwd())
dir = os.path.dirname(os.path.abspath(__file__))

with open(dir+r'\config.txt', 'r') as con:
    subject_id = con.readline().strip()
    interval = int(con.readline().strip())

class TouchInput(Widget):

    def on_touch_down(self, touch):
        if touch.device == TOUCH_SCREEN:
            data.append([subject_id, touch.id, time.time() * 100000])

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
    Window.fullscreen = True
    Window.exit_on_escape = True
    MyApp().run()
