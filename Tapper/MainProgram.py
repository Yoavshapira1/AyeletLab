import re
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout

# TODO: check integration with the Tapper software, consider using Screen instead of Widget
# TODO: organize first screen

current_subject_dir = ""

class EnterSubjectName(Screen):

    wrong_name_msg = '"Invalid name!"\nName should contain only\nletters, digits, and the characters:\n _ ,  - ,  . ,  \''
    name_reg = re.compile("^[\w\-. ]+$")

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='horizontal'
        self.spacing=80

        self.txt = TextInput(hint_text='Enter a subject name', size_hint=(.5,.1))
        self.add_widget(self.txt)

        self.btn = Button(text='Enter', on_press=self.enter_subject_name, size_hint=(.1, .1))
        self.add_widget(self.btn)

    def enter_subject_name(self, instance):
        if not self.name_reg.match(self.txt.text):
            popup = Popup(title="Error",  content=Label(text=self.wrong_name_msg),
                      size_hint=(0.35, 0.25))
            popup.open()
        else:
            self.create_subject_directory(self.txt.text)

    def create_subject_directory(self, subject_name):
        i = 0
        while True:
            if os.path.isdir(subject_name + r"_%d" % i):
                i += 1
            else:
                break
        os.mkdir(subject_name + r"_%d" % i)
        global current_subject_dir
        current_subject_dir = subject_name + r"_%d" % i
        self.screen_manager.current = "menu"

class MenuLayOut(BoxLayout):
    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='vertical'
        self.spacing=20

        self.tapper_btn = Button(text="Tapper", on_press=self.start_tapper)
        self.add_widget(self.tapper_btn)

        self.motion_btn = Button(text="Motions", on_press=self.to_motion)
        self.add_widget(self.motion_btn)

        self.exit_btn = Button(text="Exit", on_press=self.exit)
        self.add_widget(self.exit_btn)

    def start_tapper(self, *args):
        self.screen_manager.current = "tapper"

    def to_motion(self, *args):
        self.screen_manager.current = "motion"

    def exit(self, *args):
        w = self.screen_manager.get_root_window()
        App.get_running_app().stop()
        w.close()

class MenuScreen(Screen):

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.menu = MenuLayOut(sm)
        self.add_widget(self.menu)

class TapperScreen(Screen):
    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm

        self.menu_btn = Button(text="This is a Tapper. Press to back to menu", on_press=self.to_menu)
        self.add_widget(self.menu_btn)

    def to_menu(self, *args):
        self.screen_manager.current = "menu"

class MotionScreen(Screen):
    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm

        self.menu_btn = Button(text="This is a Motion. Press to back to menu", on_press=self.to_menu)
        self.add_widget(self.menu_btn)

    def to_menu(self, *args):
        self.screen_manager.current = "menu"


class MyApp(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(EnterSubjectName(name="name", sm=screen_manager))
        screen_manager.add_widget(MenuScreen(name="menu", sm=screen_manager))
        screen_manager.add_widget(TapperScreen(name="tapper", sm=screen_manager))
        screen_manager.add_widget((MotionScreen(name="motion", sm=screen_manager)))
        return screen_manager

if __name__ == "__main__":
    Window.exit_on_escape = True
    # Run the app - results in creating new directory
    try:
        MyApp().run()

    # If a file hasn't created in the directory - delete it
    except Exception as e:
        print(e)

    if not os.listdir(current_subject_dir):
        os.rmdir(current_subject_dir)