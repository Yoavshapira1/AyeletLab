from csv import writer
from re import compile
from os import rmdir, listdir, mkdir, getcwd, chmod
from os.path import isdir
from time import time
from kivy.app import App
from kivy.clock import Clock, ClockEvent
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from util import *

# python list are accessible to use and change at any time
# that is why some of the variable are as lists
# these to be change in the WelcomeScreen and used in Recorders objects, which write the files
subject = [""]

time_for_tapping = ["60"]
TAPPER_inst =  "In the next session you will need to tap the screen in a constant frequency, as much as you can. " \
                "\nTap on the screen to start the session."

time_for_free_motion = ["60"]
FREE_MOTION_inst =  "In the next session you will need to move freely on the screen." \
               "\nTap on the screen to start the session."

time_for_circles = ["60"]
CIRCLES_inst =  "In the next session you will need to draw circles. " \
                "\nTap on the screen to start the session."

reg = "^[1-9]\d*$"
tapper_timer_err_msg = '"Value must be a positive integer'
tapper_timer_do_msg = "Duration of the Tapping task trial.\nDefault is %s seconds" % time_for_tapping[0]

motion_timer_err_msg = '"Value must be a positive integer'
motion_timer_do_msg = "Duration of the Motion task trial.\nDefault is %s seconds" % time_for_free_motion[0]

class EnterText(BoxLayout):
    """Abstract box layout for changing one of the trial's parameters"""

    def __init__(self, sm, do_msg, err_msg, regex, value_to_change, **kwargs):
        """
        :param sm: <Screen Manager>
        :param size_hint_y: <float> Relative size on y axis
        :param do_msg: <String> tells the user what this box does
        :param err_msg: <String> raise the user a typo error
        :param regex: <String> regex represents the acceptable input
        :param value_to_change: <List> a list contain single value, which is the value to be change by the user
        """
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.orientation='horizontal'
        self.msg = do_msg
        self.err_msg = err_msg
        self.re = compile(regex)
        self.value_to_change = value_to_change          # this is a list contains 1 element

        self.txt = TextInput(hint_text=self.msg, size_hint=(.8, 1.))
        self.add_widget(self.txt)

        self.btn = Button(text='Enter', on_press=self.change_value, size_hint=(.2, 1.))
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
    """Specific instance of EnterText abstraction, for changing the subject's name"""

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
            if isdir("Data/" + self.txt.text + r"_%d" % i):
                i += 1
            else:
                break
        self.value_to_change[0] = self.txt.text + r"_%d" % i
        mkdir("Data/" + self.value_to_change[0])
        self.screen_manager.current = MENU

class EnterInteger(EnterText):
    """Specific instance of EnterText abstraction, for changing the integer values of the trial"""

    reg = "^[1-9]\d*$"
    err = 'Value must be a positive integer'
    do = "Enter a timer for the %s mission interval.\nDefault is %s"

    def __init__(self, task, value_to_change, **kwargs):
        super().__init__(do_msg=self.do % (task, value_to_change[0]), err_msg=self.err, regex=self.reg, value_to_change=value_to_change, **kwargs)

class MenuScreen(Screen):
    """The main menu screen"""

    instructions = "For [b][i]Tapper[/i][/b] task: press '1'\n" \
                   "For [b][i]Circles[/i][/b] task: press '2'\n" \
                   "For [b][i]Free Motion[/i][/b]: press '3'\n\n\n\n\n" \
                   "For exit anytime, press 'Escape'"

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.add_widget(Label(text=self.instructions, font_size=26, markup=True))

    def on_enter(self):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == '1':
            self._keyboard_closed()
            self.screen_manager.current = TAPPER

        if keycode[1] == '2':
            self._keyboard_closed()
            self.screen_manager.current = CIRCLES

        if keycode[1] == '3':
            self._keyboard_closed()
            self.screen_manager.current = FREE_MOTION

class Task(Widget):
    """An abstract object which represents a single task,
    i.e TapperTask, MotionTask etc..."""

    def __init__(self, dir, **kwargs):
        """
        :param dir: <List> contains a single String represents the name of the
        directory to save the file in
        Hence, the directory should be access by: 'self.dir[0]'
        """
        super().__init__(**kwargs)
        self.dir = dir        # this is a list in length 1

    def _start(self, file_name, counter, first_row):
        self.tapNum = 0
        path = getcwd() + '\Data\%s\%s.csv' % (self.dir[0], file_name + "_" + str(counter))
        chmod(getcwd(), 0o777)
        self.file = open(path, 'w+', newline='')
        self.writer = writer(self.file)
        self.writer.writerow(first_row)

    def stop(self):
        pass

    def on_touch_down(self, touch):
        pass

    def write_perception(self, real_time, subject_perception):
        self.writer.writerow([])
        self.writer.writerow([])
        self.writer.writerow(['Time elapsed (in seconds): ', real_time])
        self.writer.writerow(['Subject perception (in seconds): ', subject_perception])
        self.file.close()

class TapperTask(Task):
    """Represents the Tapping task"""

    counter = 0
    file_name = TAPPER
    first_row = CSV_COLS_PER_TASK[TAPPER]

    def __init__(self, dir, **kwargs):
        super().__init__(dir=dir, **kwargs)
        self.dir = dir        # this is a list in length 1

    def start(self):
        self.counter += 1
        super()._start(self.file_name, self.counter, self.first_row)

    def on_touch_down(self, touch):
        self.tapNum += 1
        self.writer.writerow([self.dir[0], self.tapNum, time() * 1000])


class FreeMotionWrapper(Task):
    """a Wrapper for the Free motion tasks; i.e. MotionTask & CirclesTask"""

    counter = 0
    first_row = CSV_COLS_PER_TASK[FREE_MOTION]

    def __init__(self, dir, file_name, **kwargs):
        """
        :param dir: <List> contains a single String represents the name of the directory to save the file in
        Hence, the directory should be access by: 'self.dir[0]'
        """
        super().__init__(dir=dir, **kwargs)
        self.dir = dir             # this is a list in length 1
        self.file_name = file_name

    def start(self):
        self.touch = None
        self.counter += 1
        super()._start(self.file_name, self.counter, self.first_row)
        self.event = Clock.schedule_interval(self.write, 0.001)

    def on_touch_down(self, touch):
        self.tapNum += 1
        self.touch = touch

    def on_touch_move(self, touch):
        if self.tapNum == 0:
            self.tapNum = 1
            self.touch = touch

    def on_touch_up(self, touch):
        self.touch = None

    def write(self, *args):
        if self.touch:
            self.writer.writerow([self.dir[0], self.tapNum, self.touch.sx, self.touch.sy, time() * 1000])
        else:
            self.writer.writerow([self.dir[0], -1, -1, -1, time() * 1000])

    def stop(self):
        ClockEvent.cancel(self.event)


class MotionTask(FreeMotionWrapper):
    """This object should be in used by the FreeMotionWrapper, by delegation"""

    file_name = FREE_MOTION
    def __init__(self, dir, **kwargs):
        super().__init__(dir=dir, file_name=self.file_name, **kwargs)


class CirclesTask(FreeMotionWrapper):
    """This object should be in used by the FreeMotionWrapper, by delegation"""

    file_name = CIRCLES
    def __init__(self, dir, **kwargs):
        super().__init__(dir=dir, file_name=self.file_name, **kwargs)


class TaskScreenWrapper(Screen):
    """
    A wrapper for the different kinds of tasks. (i.e. Tapper, FreeMotion).
    Making a new instance of one of those should use this wrapper.
    """

    def __init__(self, sm, time, task, instructions, **kwargs):
        """
        :param sm: <Screen Manager>
        :param time: <List> contains a single integer - time, in seconds, for the task to run
        :param file_name: <String> the name of the file which is created by the task
        :param task: <Widget> this is the task that run in the background, and record the touch inputs
        :param instructions: <String> instructions for the user
        """
        super().__init__(**kwargs)
        self.screen_manager = sm
        self.time = time
        self.task = task(dir=subject)
        self.instructions = instructions

    def on_enter(self):
        """ Initiates keyboard listener, and show welcome screen"""
        welcome = Button(text=self.instructions, on_touch_down=self.program)
        self.add_widget(welcome)

    def program(self, *args):
        """ run the current program """
        self.clear_widgets()
        self.add_widget(self.task)
        self.task.start()
        Clock.schedule_once(self.take_perception, int(self.time[0]))

    def take_perception(self, *args):
        """ presents a message about ending the session and back to Menu """
        self.task.stop()
        self.clear_widgets()
        end = TextInput(hint_text="How long was this session for? Type and then press 'Enter'",
                        input_filter='int', size_hint=(0.2, 0.1), pos_hint={'top': 1.},
                        multiline=False, on_text_validate=self.end)
        self.popup = Popup(title='Sessions ended!', content=end, size_hint=(.5, .5), auto_dismiss = False)
        self.popup.open()

    def end(self, text_input, *args):
        self.popup.dismiss()
        self.task.write_perception(self.time[0], "N/A" if text_input.text == "" else text_input.text)
        self.clear_widgets()
        self.screen_manager.current = MENU

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(Screen(name='settings'))
        setting_scr = sm.get_screen('settings')
        main_layout = GridLayout(rows=4, orientation='tb-lr')
        setting_layout = GridLayout(rows=5, orientation='tb-lr')

        # Timers setting
        setting_layout.add_widget(Label(text='Timers setting. Do not enter anything if you want the default values.'))
        setting_layout.add_widget(EnterInteger(sm=sm, task=TAPPER, value_to_change=time_for_tapping))
        setting_layout.add_widget(EnterInteger(sm=sm, task=CIRCLES, value_to_change=time_for_circles))
        setting_layout.add_widget(EnterInteger(sm=sm, task=FREE_MOTION, value_to_change=time_for_free_motion))

        # Subject name setting
        setting_layout.add_widget(Label(text='Name of subject must be filled'))
        main_layout.add_widget(setting_layout)
        main_layout.add_widget(EnterName(sm=sm, value_to_change=subject))

        # Build the setting Screen
        setting_scr.add_widget(main_layout)

        # Build the different Screens, for the different tasks
        sm.add_widget(MenuScreen(name=MENU, sm=sm))
        sm.add_widget(TaskScreenWrapper(name=TAPPER, sm=sm, time=time_for_tapping, task=TapperTask, instructions=TAPPER_inst))
        sm.add_widget(TaskScreenWrapper(name=FREE_MOTION, sm=sm, time=time_for_free_motion, task=MotionTask, instructions=FREE_MOTION_inst))
        sm.add_widget(TaskScreenWrapper(name=CIRCLES, sm=sm, time=time_for_circles, task=CirclesTask, instructions=CIRCLES_inst))
        return sm

if __name__ == "__main__":

    # Create a directory where the results will be saved in
    if not isdir("Data"):
        mkdir("Data")

    # Avoiding the user from accidentally close the app
    # App closes ONLY if <escape> is pressed
    Window.fullscreen = True
    Window.borderless = True
    Window.maximize()
    Window.exit_on_escape = True

    # uncomment this to print Exception to error console
    MyApp().run()

    # Run the app - results in creating new directory
    try:
        MyApp().run()

    except Exception as e:
        print(e)

    # If a file hasn't created in the directory - delete it
    dir = "Data/" + subject[0]
    if not listdir(dir):
        rmdir(dir)