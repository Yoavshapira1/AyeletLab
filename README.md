# INSTALLATION:
1) Make sure _**python**_ and _**pip**_ are installed and are in the variables path
2) Build an environment using the _**requirements.txt**_ file.
3) Now you can run the app using your DAW and the virtual environment.
However, `Kivy` is also need to be added to path variables in order to run the app from the terminal, and pack it. 

**If you want to use libusb (which we don't at the moment):**
1) Access the libusb directory.
2) Copy MS32\dll\libusb-1.0.dll to C:\Windows\SysWOW64 .
3) Copy MS64\dll\libusb-1.0.dll to C:\Windows\System32.
4) *"pip install libusb"* in the terminal.
5) Copy MS32\dll\libusb-1.0.dll to #your venv#\Lib\site-packages\libusb_platform_windows\x86 
6) Copy MS64\dll\libusb-1.0.dll to: #your venv#\Lib\site-packages\libusb_platform_windows\x64

# USB devices notes:
The program ATM uses Kivy package to handle input from usb touch devices, so the _libusb_ library is not in use at all.
**If you do want to use it**, in order to access the usb device **manually**, the driver of the device must be of 'libusb'.
If you encounter with this error:
*"usb.core.USBError: [Errno 5] Input/Output Error"*
It means the device cannot be accessed for the mentioned reason. 
In this case, use zadig-2.7.exe (under *Touch Utilities*) to change the driver. Link for instructions:
https://github.com/pbatard/libwdi/wiki/Zadig

Useful links:

#Applications development:
https://labstreaminglayer.readthedocs.io/dev/app_dev.html

#LSL in GitHub:
https://github.com/sccn/labstreaminglayer

#libusb docs:
https://libusb.sourceforge.io/api-1.0/

#PyUSB docs on GitHub:
https://github.com/walac/pyusb/blob/master/docs/tutorial.rst

# osc4py3 Documentation:
https://osc4py3.readthedocs.io/en/latest/

# creating .exe from .py uses kivy features:
- first make sure you have installed the venv properly:
	https://kivy.org/doc/stable/gettingstarted/installation.html#kivy-source-install
- then follow this guidence:
	https://kivy.org/doc/stable/guide/packaging-windows.html#packaging-a-simple-app