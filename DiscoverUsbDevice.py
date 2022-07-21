#!/usr/bin/python
import sys
import usb.core

def make_list(dict):
  # find USB devices
  dev = usb.core.find(find_all=True)
  # loop through devices, printing vendor and product ids in decimal and hex
  for cfg in dev:
    dict[str(cfg.idProduct)] = {'Decimal VendorID' : str(cfg.idVendor), 'DecProductID:' : str(cfg.idProduct),
                               'Hexadecimal VendorID' : hex(cfg.idVendor), 'HexProductID:' : hex(cfg.idProduct)}
    # sys.stdout.write('Decimal VendorID=' + str(cfg.idVendor) + ' & ProductID=' + str(cfg.idProduct) + '\n')
    # sys.stdout.write('Hexadecimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n\n')


if __name__ == "__main__":
  plugged, unplugged = {}, {}
  input("PLUG the device to be discovered and press ENTER to continue...")
  make_list(plugged)
  input("UNPLUG the device and press ENTER to continue...")
  make_list(unplugged)
  print("USB devices that were unplugged:")
  for k in plugged:
    if k not in unplugged.keys():
      print(plugged[k])