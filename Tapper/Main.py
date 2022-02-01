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
from  kivy.uix.gridlayout import *

# TODO: create sub-classes for screens including the required strings

# python list are accessible to use and change at any time
# that is why some of the variable are as lists
# these to be change in the WelcomeScreen and used in Recorders objects, which write the files
subject = [""]

MENU = "Menu"
ENTER_NAME = "Name"
TAPPER = "Tapper"
FREE_MOTION = "Motion"

time_for_tapping = ["60"]
TAPPER_inst =  "In the next session you will need to tap the screen in a constant frequency, as much as you can. " \
                "\nTap on the screen to start the session."

time_for_free_motion = ["10"]
FREE_MOTION_inst =  "In the next session you will need to move freely on the screen." \
               "\nTap on the screen to start the session."

reg = "^[1-9]\d*$"
tapper_timer_err_msg = '"Value must be a positive integer'
tapper_timer_do_msg = "Enter a positive integer for the Tapper interval.\nDefault is %s" % time_for_tapping[0]

motion_timer_err_msg = '"Value must be a positive integer'
motion_timer_do_msg = "Enter a positive integer for the Motion interval.\nDefault is %s" % time_for_free_motion[0]

class EnterText(BoxLayout):

    def __init__(self, sm, size_hint_y, do_msg, err_msg, regex, value_to_change, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='horizontal'
        self.msg = do_msg
        self.err_msg = err_msg
        self.re = re.compile(regex)
        self.value_to_change = value_to_change          # this is a list contains 1 element

        self.txt = TextInput(hint_text=self.msg, size_hint=(.8, size_hint_y))
        self.add_widget(self.txt)

        self.btn = Button(text='Enter', on_press=self.change_value, size_hint=(.2, size_hint_y))
        self.add_widget(self.btn)

    def change_value(self, instance):
        if not self.re.match(self.txt.text):
            popup = Popup(title="Error",  content=Label(text=self.err_msg),
                      size_hint=(0.35, 0.25))
            popup.open()
            self.txt.text = ""
        else:
            self.value_to_change[0] = self.txt.text


class EnterName(EnterText):

    name_err_msg = '"Invalid name!"\nName should contain only\nletters, digits, and the characters:\n _ ,  - ,  . ,  \''
    name_do_msg = "enter a name"
    name_regex = "^[\w\-. ]+$"

    def __init__(self, **kwargs):
        super().__init__(do_msg=self.name_do_msg, err_msg=self.name_err_msg, regex=self.name_regex, **kwargs)

    def change_value(self, instance):
        if not self.re.match(self.txt.text):
            popup = Popup(title="Error",  content=Label(text=self.err_msg),
                      size_hint=(0.35, 0.25))
            popup.open()
            self.txt.text = ""
        else:
            self.value_to_change[0] = self.txt.text
            self.create_subject_directory()

    def create_subject_directory(self):
        i = 0
        while True:
            if os.path.isdir(self.txt.text + r"_%d" % i):
                i += 1
            else:
                break
        self.value_to_change[0] = self.txt.text + r"_%d" % i
        os.mkdir(self.value_to_change[0])
        self.screen_manager.current = MENU

class EnterInteger(EnterText):

    reg = "^[1-9]\d*$"
    err = 'Value must be a positive integer'
    do = "Enter a timer for the %s mission interval.\nDefault is %s"

    def __init__(self, task, def_value, **kwargs):
        super().__init__(do_msg=self.do % (task, def_value), err_msg=self.err, regex=self.reg, **kwargs)

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
        self.layOut = EnterText(sm)
        self.add_widget(self.layOut)

class MenuScreen(Screen):

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.menu = MenuLayOut(sm)
        self.add_widget(self.menu)

class Tapper(Widget):

    def __init__(self, name, file_name, **kwargs):
        super().__init__(**kwargs)
        self.name = name        # this is a list in length 1
        self.file_name = file_name
        self.tapNum = 0

    def start(self):
        self.name = self.name[0]
        self.file = open(os.path.curdir + '\%s\%s.csv' % (self.name, self.file_name), 'w', newline='')
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
        self.name = name             # this is a list in length 1
        self.file_name = file_name
        self.tapNum = 0
        self.touch = None

    def start(self):
        self.name = self.name[0]
        self.file = open(os.path.curdir + '\%s\%s.csv' % (self.name, self.file_name), 'w', newline='')
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
        self.time = int(self.time[0])
        print(self.time)
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
        sm = ScreenManager()
        sm.add_widget(Screen(name='welcome'))
        welcome_scr = sm.get_screen('welcome')
        main_layout = GridLayout(rows=3, orientation='tb-lr')
        setting_layout = GridLayout(rows=4, orientation='tb-lr')

        setting_layout.add_widget(Label(text='Timers setting. Do not enter anything if you want the default values.'))
        setting_layout.add_widget(EnterInteger(sm=sm, size_hint_y=1., task=TAPPER, def_value=time_for_tapping[0],
                                               value_to_change=time_for_tapping))
        setting_layout.add_widget(EnterInteger(sm=sm, size_hint_y=1., task=FREE_MOTION, def_value=time_for_free_motion[0],
                                               value_to_change=time_for_free_motion))
        setting_layout.add_widget(Label(text='Name of subject must be filled'))

        main_layout.add_widget(setting_layout)
        main_layout.add_widget(EnterName(sm=sm, size_hint_y=1., value_to_change=subject))

        welcome_scr.add_widget(main_layout)

        sm.add_widget(MenuScreen(name=MENU, sm=sm))
        sm.add_widget(RecorderScreen(name=TAPPER, sm=sm, time=time_for_tapping, file_name=TAPPER, recorder=Tapper, instructions=TAPPER_inst))
        sm.add_widget(RecorderScreen(name=FREE_MOTION, sm=sm, time=time_for_free_motion, file_name=FREE_MOTION, recorder=FreeMotion, instructions=FREE_MOTION_inst))

        return sm

if __name__ == "__main__":
    Window.exit_on_escape = True
    Window.fullscreen = False
    # uncommenting this, create a directory even if it's empty
    # MyApp().run()

    # Run the app - results in creating new directory
    try:
        MyApp().run()

    # If a file hasn't created in the directory - delete it
    except Exception as e:
        print(e)

    if not os.listdir(*subject):
        os.rmdir(*subject)