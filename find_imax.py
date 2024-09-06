"""
Searches for the FrSky Imax B6 Mini charger device

Requires pyusb module installed, but first libusb-1.0 must be installed from the zip or 7z achive file. 
There are two subdirectries in archive for 64 bit or 32 bit system. Copy the three 
libusb.-1.0 files, including the .dll to the script folder containing this module,
 if the intention is to import the libusb files into python from the
script directory. However, for more generality copy the three files to
C:/windows/system32 and for 64 bit system also copy to C:/windows/syswow64.

Below is how not place the dll and other files into the window's folders:
import usb.backend.libusb1
backend = usb.backend.libusb1.get_backend(find_library=lambda x: "F:\rd_codes\libusb-1.0.dll")
dev = usb.core.find(backend=backend)

Next install pysub using: pip install pyusb
The tutorial on pyusb
https://github.com/pyusb/pyusb/blob/master/docs/tutorial.rst
"""

#to get all usb devices run following from an independent python module
#!/usr/bin/python
import sys
import usb.core
import usb.util
import usb

def get_device_configuration():
  print('IMAX DEVICE TESTING:')
  try:
    dev = usb.core.find(idVendor=0x0000, idProduct=0x0001)
    print('Decimal VendorID=' + hex(dev.idVendor) + ' & ProductID=' + hex(dev.idProduct) + '\n')
    #gets real messy for the imax usb; the idVendor and idProduct are not in cfg or 
    if dev: 
      print('device found: ', dev)
  except:
    print('No device with Vendor id: 0x000; Product id: 0x0001 found')
    print('Is device connected? Is device on?')


get_device_configuration()
