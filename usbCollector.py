import sys

import usb.core
import usb.util
import numpy as np

# Those are the Vendor ID and the Product ID of the hardware:
# To find those values, go to:
# 'Device Manager' >>> 'Universal Serial Bus Controllers' >>> Select your device (Notice that there might be
# several devices with the same name - Make sure you choose the right one) and double click >>> 'Details' Tab >>>
# >>> From roll menu choose 'Hardware IDs' >>> The first line should be as the template:
# USB\VID_<VENDOR_ID>&PID_<PRODUCT_ID>&REV_***
VENDOR_ID = 0x0eef
PRODUCT_ID = 0xC002


    ################################# PyUSB ################################

def PyUSB_func():

    # find our device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    # dev = usb.core.find(find_all=True)

    # was it found?
    if dev is None:
        raise ValueError('Device not found')


    # set the active configuration. With no arguments, the first
    # configuration will be the active one
    dev.set_configuration()

    # get an endpoint instance
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]

    ep = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

    assert ep is not None

    # write the data
    ep.write('test')

    ################################# libusb ################################

# def liusb_func():
#     with usb1.USBContext() as context:
#         handle = context.openByVendorIDAndProductID(
#             VENDOR_ID,
#             PRODUCT_ID,
#             skip_on_error=True,
#         )
#         if handle is None:
#             # Device not present, or user is not allowed to access device.
#             pass
#         with handle.claimInterface("INTERFACE"):
#             # Do stuff with endpoints on claimed interface.
#             pass


if __name__ == "__main__":
    PyUSB_func()


