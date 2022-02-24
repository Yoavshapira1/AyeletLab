from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.app import App


class MyWidget(BoxLayout):

    def __init__(self,**kwargs):
        super(MyWidget,self).__init__(**kwargs)

        self.orientation = "vertical"

        self.name_input = TextInput(text='name')

        self.add_widget(self.name_input)

        self.save_button = Button(text="Save")
        self.save_button.bind(on_press=self.save)

        self.save_popup = SaveDialog(self) # initiation of the popup, and self gets passed

        self.add_widget(self.save_button)


    def save(self,*args):
        self.save_popup.open()


class SaveDialog(Popup):

    def __init__(self,my_widget,**kwargs):  # my_widget is now the object where popup was called from.
        super(SaveDialog,self).__init__(**kwargs)

        self.my_widget = my_widget

        self.content = BoxLayout(orientation="horizontal")

        self.save_button = Button(text='Save')
        self.save_button.bind(on_press=self.save)

        self.cancel_button = Button(text='Cancel')
        self.cancel_button.bind(on_press=self.cancel)

        self.content.add_widget(self.save_button)
        self.content.add_widget(self.cancel_button)

    def save(self,*args):
        print ("save %s" % self.my_widget.name_input.text) # and you can access all of its attributes
        #do some save stuff
        self.dismiss()

    def cancel(self,*args):
        print ("cancel")
        self.dismiss()


class MyApp(App):

    def build(self):
        return MyWidget()

if __name__ == "__main__":

    MyApp().run()