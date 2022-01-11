import time
import re
import os
from kivy.app import App
from kivy.lang import  Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from functools import partial
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
import csv

current_subject_dir = ""

class EnterSubjectName(BoxLayout):

    wrong_name_msg = '"Invalid name!"\nName should contain only\nletters, digits, and the characters:\n _ ,  - ,  . ,  \''
    name_reg = re.compile("^[\w\-. ]+$")

    def __init__(self, **kwargs):
        super(EnterSubjectName, self).__init__(**kwargs)
        self.orientation='horizontal'
        self.spacing=20

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
        self.root.current = "menu_screen"

Builder.load_string("""
<MenuScreen>:
    BoxLayout:
        Button:
            text: "Go to Tapper"
            on_press:
                root.manager.transition.direction = 'left'
                root.manager.current = "tapper"
                
<TapperScreen>:
    BoxLayout:
        Button:
            text: "This is a Tapper. Click to go back to menu"
            on_press:
                root.manager.transition.direction = 'left'
                root.manager.current = "menu"
""")

class SubjectNameScreen(Screen):
    def __init__(self, **kwargs):
        super(SubjectNameScreen, self).__init__()
        self.add_widget(EnterSubjectName())

class MenuScreen(Screen):
    pass

class TapperScreen(Screen):
    pass

screen_manager = ScreenManager()
screen_manager.add_widget(SubjectNameScreen(name="name"))
screen_manager.add_widget(MenuScreen(name="menu"))
screen_manager.add_widget(TapperScreen(name="tapper"))

class Menu(Widget):
    def __init__(self):
        super(Menu, self).__init__()
        self.btn = Button(text="text")
        self.add_widget(self.btn)

    def build(self):
        return Button()

class MyApp(App):
    def build(self):
        return screen_manager

if __name__ == "__main__":
    # Run the app - results in creating new directory
    try:
        MyApp().run()

    # If a file hasn't created in the directory - delete it
    except Exception as e:
        print(e)

    if not os.listdir(current_subject_dir):
        os.rmdir(current_subject_dir)