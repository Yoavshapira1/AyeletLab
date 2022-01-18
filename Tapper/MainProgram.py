import csv
import re
import os
import time
from kivy._clock import ClockEvent
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

# TODO: subject name doesn't appear

subject = ""

MENU = "Menu"
ENTER_NAME = "Name"
TAPPER = "Tapper"
FREE_MOTION = "Motion"

time_for_tapping = 5
TAPPER_inst =  "In the next session you will need to tap the screen in a constant frequency, as much as you can." \
               "\nThe session will last for %d seconds. \nTap on the screen to start the session." % time_for_tapping

time_for_free_motion = 5
FREE_MOTION_inst =  "In the next session you will need to tap the screen in a constant frequency, as much as you can." \
               "\nThe session will last for %d seconds. \nTap on the screen to start the session." % time_for_free_motion


class EnterSubjectNameLayOut(BoxLayout):

    wrong_name_msg = '"Invalid name!"\nName should contain only\nletters, digits, and the characters:\n _ ,  - ,  . ,  \''
    name_reg = re.compile("^[\w\-. ]+$")

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='horizontal'
        self.spacing=20

        self.txt = TextInput(hint_text='Enter a subject name', size_hint=(.8, .1))
        self.add_widget(self.txt)

        self.btn = Button(text='Enter', on_press=self.enter_subject_name, size_hint=(.2, .1))
        self.add_widget(self.btn)

    def enter_subject_name(self, instance):
        if not self.name_reg.match(self.txt.text):
            popup = Popup(title="Error",  content=Label(text=self.wrong_name_msg),
                      size_hint=(0.35, 0.25))
            popup.open()
            self.txt.text = ""
        else:
            self.create_subject_directory(self.txt.text)

    def create_subject_directory(self, subject_name):
        i = 0
        while True:
            if os.path.isdir(subject_name + r"_%d" % i):
                i += 1
            else:
                break
        global subject
        subject = subject_name + r"_%d" % i
        os.mkdir(subject)
        self.screen_manager.current = MENU

class MenuLayOut(BoxLayout):
    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='vertical'
        self.spacing=20

        self.tapper_btn = Button(text="Tapper", on_press=self.to_tapper)
        self.add_widget(self.tapper_btn)

        self.motion_btn = Button(text="Free Motions", on_press=self.to_motion)
        self.add_widget(self.motion_btn)

        self.exit_btn = Button(text="Exit", on_press=self.exit)
        self.add_widget(self.exit_btn)

    def to_tapper(self, *args):
        self.screen_manager.current = TAPPER

    def to_motion(self, *args):
        self.screen_manager.current = FREE_MOTION

    def exit(self, *args):
        w = self.screen_manager.get_root_window()
        App.get_running_app().stop()
        w.close()

class EnterSubjectName(Screen):

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.layOut = EnterSubjectNameLayOut(sm)
        self.add_widget(self.layOut)

class MenuScreen(Screen):

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.menu = MenuLayOut(sm)
        self.add_widget(self.menu)

class Tapper(Widget):

    def __init__(self, name, file_name, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.file_name = file_name
        self.tapNum = 0

    def start(self):
        self.file = open(os.path.curdir + '\%s\%s.csv' % (subject, self.file_name), 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['subject', 'tapNum', 'natRhythmTap'])

    def on_touch_down(self, touch):
        self.tapNum += 1
        self.writer.writerow([self.name, self.tapNum, time.time() * 1000])

    def destroy(self):
        self.file.close()

class FreeMotion(Widget):

    def __init__(self, name, file_name, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.file_name = file_name
        self.tapNum = 0
        self.touch = None

    def start(self):
        self.file = open(os.path.curdir + '\%s\%s.csv' % (subject, self.file_name), 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['subject', 'tapNum', 'x_pos', 'y_pos', 'time_stamp'])
        self.event = Clock.schedule_interval(self.write, 0.001)

    def on_touch_down(self, touch):
        self.tapNum += 1
        self.touch = touch

    def write(self, *args):
        if self.touch:
            self.writer.writerow([self.name, self.tapNum, self.touch.sx, self.touch.sy, time.time() * 1000])
        else:
            self.writer.writerow([self.name, -1, -1, -1, time.time() * 1000])

    def on_touch_up(self, touch):
        self.touch = None

    def destroy(self, *args):
        ClockEvent.cancel(self.event)
        self.file.close()

class RecorderScreen(Screen):

    def __init__(self, sm, time, file_name, recorder, instructions, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.time = time
        self.rec = recorder(subject, file_name)
        self.instructions = instructions
        self.welcome()

    def welcome(self, *args):
        """ presents a welcome screen, including instructions """
        welcome = Button(text=self.instructions, on_press=self.program)
        self.add_widget(welcome)

    def program(self, *args):
        """ run the current program """
        self.clear_widgets()
        self.add_widget(self.rec)
        self.rec.start()
        Clock.schedule_once(self.end, self.time)

    def end(self, *args):
        """ presents a message about ending the session and back to Menu """
        self.rec.destroy()
        self.clear_widgets()
        end = Label(text="Sessions ended!")
        self.add_widget(end)
        Clock.schedule_once(self.back_to_menu, 3)

    def back_to_menu(self, *args):
        menu_btn = Button(text="Session ended. Click here to go back to menu", on_press=self.to_menu)
        self.add_widget(menu_btn)

    def to_menu(self, *args):
        self.screen_manager.current = MENU

class MyApp(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(EnterSubjectName(name=ENTER_NAME, sm=screen_manager))
        screen_manager.add_widget(MenuScreen(name=MENU, sm=screen_manager))
        screen_manager.add_widget(RecorderScreen(name=TAPPER, sm=screen_manager, time=time_for_tapping, file_name=TAPPER, recorder=Tapper, instructions=TAPPER_inst))
        screen_manager.add_widget(RecorderScreen(name=FREE_MOTION, sm=screen_manager, time=time_for_free_motion, file_name=FREE_MOTION, recorder=FreeMotion, instructions=FREE_MOTION_inst))
        return screen_manager

if __name__ == "__main__":
    Window.exit_on_escape = True
    Window.fullscreen = False
    MyApp().run()
    # Run the app - results in creating new directory
    try:
        MyApp().run()

    # If a file hasn't created in the directory - delete it
    except Exception as e:
        print(e)

    if not os.listdir(subject):
        os.rmdir(subject)