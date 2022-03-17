from kivy.app import App
import numpy as np
from kivy.uix.widget import Widget
import Hilbert_Curve_Table

x = []
y = []

class MyWidget(Widget):

    def on_touch_move(self, touch):
        global x, y
        x.append(touch.spos[0])
        y.append(touch.spos[1])

class MyApp(App):

    def build(self):
        return MyWidget()

if __name__ == "__main__":
    # with open("hilbert_2048.txt", "w+") as f:
    #     f.write(str(Hilbert_Curve_Table.create_table(2048)))
    # dic = Hilbert_Curve_Table.table
    # N = len(dic.keys())
    # inter = np.linspace(0.0, 1.0 - (1/N) ,N)
    # a = np.array([0.2])
    # print(np.interp(inter, a, a))

    MyApp().run()
    a = np.column_stack((x, y))
    print(np.unique(a,axis=0))
    with open("reso.txt", "w+") as f:
        f.write(str(np.unique(a)))
