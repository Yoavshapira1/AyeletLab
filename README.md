# INSTALLATION:
1) Build an environment using the requirements.txt file.
2) Access the libusb directory.
3) Copy MS32\dll\libusb-1.0.dll to C:\Windows\SysWOW64 .
4) Copy MS64\dll\libusb-1.0.dll to C:\Windows\System32.
5) *"pip install libusb"* in the terminal.
6) Copy MS32\dll\libusb-1.0.dll to #your venv#\Lib\site-packages\libusb_platform_windows\x86 
7) Copy MS64\dll\libusb-1.0.dll to: #your venv#\Lib\site-packages\libusb_platform_windows\x64

# USB collector:
The USB collector is a utility file that deals with reading data from usb device.
In order to access the usb device, the driver of the device must be of 'libusb'.
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
https://github.com/kivy/kivy/issues/5807