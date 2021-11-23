from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy import examples_dir
import multiprocessing

TOUCH_SCREEN = "WM_MotionEvent"

movements = {}

class TouchInput(Widget):

    def on_touch_down(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements[touch.id] = []
            print(touch.id, touch.ud)

    def on_touch_move(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements[touch.id].append((touch.sx, touch.sy))
            print(touch.id, touch.ud)

    def on_touch_up(self, touch):
        if type(touch).__name__ == TOUCH_SCREEN:
            movements.pop(touch.id)
            print(touch.id, touch.ud)

class MyApp(App):
    def build(self):
        return TouchInput()

if __name__ == "__main__":
    # Window.bind(on_motion=on_motion)
    MyApp().run()
