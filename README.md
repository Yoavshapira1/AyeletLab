# Intro:
...
# Setting up:
1) Make sure _**python3**_ and _**pip**_ are installed and are in the variables path. To check that, do the following:
   1) In CMD, type the command: `python`. This should print the current version of python that installed. If something like this appears:
      `'python' is not recognized as an internal or external command,
         operable program or batch file.`  then you must install python first.
   2) Repeat **i** but with the command `pip`.
2) Build a Kivy virtual environment (venv):
   1) If you are using a DAW, you can just use the _**requirements.txt**_ file while building a new venv with the DAW's wizard.
   2) Otherwise, follow these command lines:
      1) Install the venv tool. Type: `python -m pip install --upgrade pip setuptools virtualenv`
      2) Create a venv. Type `python -m virtualenv venv`
      3) Activate it. Make sure you are in the directory of the project, and then type `venv\Scripts\activate.bat` 
      4) Install the necessary modules: Make sure you have the _**requirements.txt**_ file in the directory, and then type `pip install -r requirements.txt`

**If you want to use libusb *(which we don't at the moment)*:**
1) Access the libusb directory.
2) Copy MS32\dll\libusb-1.0.dll to C:\Windows\SysWOW64 .
3) Copy MS64\dll\libusb-1.0.dll to C:\Windows\System32.
4) *"pip install libusb"* in the terminal.
5) Copy MS32\dll\libusb-1.0.dll to #your venv#\Lib\site-packages\libusb_platform_windows\x86 
6) Copy MS64\dll\libusb-1.0.dll to: #your venv#\Lib\site-packages\libusb_platform_windows\x64

You are ready to go!

# Running applications:
This guide refers to running a Kivy application through the terminal.
1) Activate the venv you built. Type: `<dir>\venv\Scripts\activate.bat` , where *dir* is the directory of the project.
2) Type `python *app.py*` in Windows (`python3 *app.py*` in Linux), where **app.py** refers to the python file of the application.

#Packing a Kivy application:
1) open CMD in the target directory.
2) activate the Kivy venv.
3) Type `pip install --upgrade pyinstaller`.
4) Type `python -m PyInstaller --name <name> <file.py>`.
5) Make sure that a file named _name.spec_ created in the target directory.
6) Add `from kivy_deps import sdl2, glew, angle` on the top of the _.spec_ file.
7) Change the lines of COLLECT in the _.spec_ file, as described here in section 3: https://kivy.org/doc/stable/guide/packaging-windows.html#packaging-a-simple-app.
8) Type `python -m PyInstaller Tapper.spec` and then `y`, if asked.
9) The executable app should appear in the directory _'dist'_.


# USB devices notes:
The program ATM uses Kivy package to handle input from usb touch devices, so the _libusb_ library is not in use at all.
**If you do want to use it**, in order to access the usb device **manually**, the driver of the device must be of 'libusb'.
If you encounter with this error:
*"usb.core.USBError: [Errno 5] Input/Output Error"*
It means the device cannot be accessed for the mentioned reason. 
In this case, use zadig-2.7.exe (under *Touch Utilities*) to change the driver. Link for instructions:
https://github.com/pbatard/libwdi/wiki/Zadig

#Useful links:
***Packing a Kivy application:***
https://kivy.org/doc/stable/guide/packaging-windows.html#packaging-a-simple-app

***Applications development:***
https://labstreaminglayer.readthedocs.io/dev/app_dev.html

***LSL in GitHub:***
https://github.com/sccn/labstreaminglayer

***libusb docs:***
https://libusb.sourceforge.io/api-1.0/

***PyUSB docs on GitHub:***
https://github.com/walac/pyusb/blob/master/docs/tutorial.rst

***osc4py3 Documentation:***
https://osc4py3.readthedocs.io/en/latest/
