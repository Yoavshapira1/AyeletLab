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

def foo():
    # find our device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    if dev is None:
        raise ValueError('device not found')
        sys.exit(1)
    else:
        print("Device Found")
        usb.util.claim_interface(dev, 0)
        dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    try:
        dev.set_configuration()
        print("Configuration set")

    except:
        print("configuration not set")

    data = dev.read(0x81, 4)
    print(data)

    usb.util.release_interface(dev, 0)

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
    print(dev[0][(0, 0)][0])
    # exit()
    # first endpoint

    endpoint = dev[0][(0, 0)][0]

    # read a data packet
    data = None
    while True:
        try:
            data = dev.read(endpoint.bEndpointAddress,
                               endpoint.wMaxPacketSize)
            print(data)

        except usb.core.USBError as e:
            print(e.errno)
            data = None
            if e.args == ('Operation timed out',):
                continue


    #
    # ep = usb.util.find_descriptor(
    #     intf,
    #     # match the first OUT endpoint
    #     custom_match= \
    #         lambda e: \
    #             usb.util.endpoint_direction(e.bEndpointAddress) == \
    #             usb.util.ENDPOINT_OUT)
    #
    # assert ep is not None

    # # write the data
    # ep.write('test')


if __name__ == "__main__":
    PyUSB_func()
    # foo()

