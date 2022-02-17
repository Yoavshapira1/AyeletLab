import csv
import os
from kivy.app import App
from kivy.uix.widget import Widget


class Base(Widget):
    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)
        path = os.getcwd() + '/file.csv'
        with open(path, 'w+', newline='') as f:
            csv.writer(f).writerow("row")
        os.chmod(path, 0o777)

class SampleApp(App):
    def build(self):
        return Base()

if __name__ == "__main__":
    SampleApp().run()
