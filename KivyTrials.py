from kivy.input import MotionEvent
from kivy.input.factory import MotionEventFactory
from kivy.input.providers.mouse import MouseMotionEventProvider
from kivy.input.providers import wm_common
from kivy.input.providers.wm_touch import WM_MotionEventProvider, WM_MotionEvent
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.config import Config
import plyer


class MyWidget(Widget):
    def on_touch_down(self, touch):
        print(touch.id)
        print(touch.uid)
        print(touch.device)
        print("**********")
        # list = MotionEventFactory.list()
        # my_prov = MotionEventFactory.get("my_provider")
        # print(my_prov)
        # wm_list = list['wm_touch']
        # print(wm_list)
        # print(touch.shape)

class MyApp(App):
    def build(self):
        MotionEventFactory.register("my_provider", WM_MotionEventProvider)
        return MyWidget()

if __name__ == "__main__":
    MyApp().run()

