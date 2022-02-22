from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.widget import Widget


class GrabMouseDemo(Widget):

    def __init__(self, **kwargs):
        super(GrabMouseDemo, self).__init__(**kwargs)
        # Window.bind(on_cursor_leave=self.cursor_leave)
        Window.bind(on_hide=self.on_hide)
        Window.bind(on_minimize=self.on_hide)
        Window.bind(on_restore=self.on_hide)

    def cursor_leave(self, window):
        print("cursor_leave:")
        Window.grab_mouse()

    def on_hide(self, window):
        Window.fullscreen = True
        Window.borderless = True
        Window.maximize()
        Window.exit_on_escape = True

    def on_touch_move(self, touch):
        print(*touch.pos)
        if not self.collide_point(*touch.pos):
            # if the touch collides with our widget, let's grab it
            touch.grab(self)

            # and accept the touch.
            return True


class TestApp(App):
    title = "Kivy Grab Mouse Demo"

    def build(self):
        return GrabMouseDemo()


if __name__ == "__main__":
    TestApp().run()