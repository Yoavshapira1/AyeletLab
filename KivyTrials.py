import os

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label


class Base(Label):
    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)
        # Window.bind(on_request_close=self.exit_check, )
        # self.counter = 0
        # self.text = str(self.counter)

    # def exit_check(self, *args):
        # self.counter += 1
        # if self.counter < 5:
        #     self.text = str(self.counter)
        #     return True  # block app's exit
        # else:
        #     return False  # let the app close
        # print("chek")


class SampleApp(App):
    def build(self):
        return Base()


if __name__ == "__main__":
    pass
