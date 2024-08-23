"""
Reads and outputs the information from the USB port of the FrSky IMAX B6 mini charger.
Some notes are specific for Windows 10, 64 bit, running python 3.6.1, which was the development environment.
Whether this code will work on other operating systems is unknown; for sure the appropriate libusb.dll must be installed.
Some notes will be overkill for experts; it helps me remember how things were done, or need to be done
Requires:
    py_usb: wihch in turn requires libusb-1.0.dll be installed first. 
    The libusb-1.0 binary files can be downlaod as zip or 7z, but will not open in Windows directly because of security.
    Open 7-Zip and using the path window to the left, open up the 7z file. Migrate to the 64 directory 
    containing the already generated libusb-1.0 files.
    There are two subdirectries in the archive: for 64 bit or 32 bit windows systems. 
    Copy the three libusb.-1.0 files, including the .dll to the folder with this script.
    Copy these files to both C:/windows/system32 and C:/windows/syswow64 for 64 bit systems.
    Alternatively, this would have been the way to get at the dll and other files, if only using 
    the script folder, e.g., f:\rc_codes:
      import usb.backend.libusb1
      backend = usb.backend.libusb1.get_backend(find_library=lambda x: "F:\rc_codes\libusb-1.0.dll")
      dev = usb.core.find(backend=backend)
    Next install pysub using: pip install pyusb
    The tutorial on pyusb https://github.com/pyusb/pyusb/blob/master/docs/tutorial.rst
"""

#to get all usb devices run following from an independent python module
#!/usr/bin/python
import os
import sys
import usb.core
import usb.util
import usb
import time
import datetime
import json
import csv

data_out = []
header = ["energy", "timer", "voltage", "current", "ext temp", "int temp", "cell 1", "cell 2", "cell 3", "cell 4", "cell 5", "cell 6"]
#Next controls time interval for quering Imax and reading returned data from the Imax usb port
query_interval = 10 #secondds
  
def output_csv(header, data_out, final_dict):
  cur_dir = os.getcwd()
  csv_file = 'imaxdata.csv'
  #Best way to get the current path of the module and file
  list_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_file)
  print('creating output')
  with open(list_file,"w")  as f:
    writer=csv.writer(f, delimiter=",", lineterminator="\r\n")
    key_list = list(final_dict.keys())
    writer.writerow(key_list)
    alist = [final_dict[k] for k in key_list]
    writer.writerow(alist)
    writer.writerow(header)  
    writer.writerows(data_out)
  print('csv file ', list_file, ' done.')   
      
class find_class(object):
  #used by find_hids(); example found online
  def __init__(self, class_):
    self._class = class_
  def __call__(self, device):
    # first, let's check the device
    if device.bDeviceClass == self._class:
      return True
    # ok, transverse all devices to find an
  # interface that matches our class
    try:
      for cfg in device:
        # find_descriptor: what's it?
        intf = usb.util.find_descriptor(
            cfg,
            bInterfaceClass=self._class
            )
        if intf is not None:
          return True
    except:
      pass
    return False

def find_our_device():
  #Finding A Particular Device
  #1.Plug in the USB device and run the code above, like python findDevices.py
  #2.Unplug the device you're trying to discover
  #3.Run python findDevices.py again
  #4.Compare the lists to find the device that disappeared between 1 and 3.
  #The below was an example with a problem, this is a very complete list of
  #the protocol settings for usb devices
  print('GETTING DEVICES AND DATA')
  #Only one bus shows up as single object, not in a list
  bus = usb.busses()
  print('devices in bus are: ', bus) #indicates a generator object
  devices = bus.devices
  print(devices)
  for dev in bus:
    print('a dev',dev)
    _name1 =usb.util.get_string(dev, dev.iSerialNumber)
    _name2 = usb.util.get_string(dev, dev.iManufacturer)
    print("device name=", _name1, ' or ', _name2)
    print( "Device:", dev.filename)
    print( "  Device class:",dev.deviceClass)
    print( "  Device sub class:",dev.deviceSubClass)
    print( "  Device protocol:",dev.deviceProtocol)
    print( "  Max packet size:",dev.maxPacketSize)
    print( "  idVendor:",hex(dev.idVendor))
    print( "  idProduct:",hex(dev.idProduct))
    print( "  Device Version:",dev.deviceVersion)
    for config in dev.configurations:
      print( "  Configuration:", config.value)
      print( "    Total length:", config.totalLength) 
      print( "    selfPowered:", config.selfPowered)
      print( "    remoteWakeup:", config.remoteWakeup)
      print( "    maxPower:", config.maxPower)
      for intf in config.interfaces:
        print( "    Interface:",intf[0].interfaceNumber)
        for alt in intf:
          print( "    Alternate Setting:",alt.alternateSetting)
          print( "      Interface class:",alt.interfaceClass)
          print( "      Interface sub class:",alt.interfaceSubClass)
          print( "      Interface protocol:",alt.interfaceProtocol)
          for ep in alt.endpoints:
            print( "      Endpoint:",hex(ep.address))
            print( "        Type:",ep.type)
            print( "        Max packet size:",ep.maxPacketSize)
            print( "        Interval:",ep.interval)


def find_hids():
  # find HID USB devices ONLY; standard usb code for Human Interface Devices (HID) is 0x03
  dev = usb.core.find(find_all=1, custom_match=find_class(3))
  #Above does find the devices, but some appear to not have any identifiable information, or restrict it
  #Had to use a try here and in the find_class to go around those special cases, whatever they are 
  for d in dev:
    try:
      print('device is: ', d)
    except:
     pass

def start_imax(): 
  #Called by __main__(); Does not set up IMAX B6 Mini; only reads the output data.
  print('IMAX DEVICE TESTING:')
  #This is specific vendor and product ids for the FrSky IMAX B6 mini with USB port
  #this will not work with the IMAX B6, which has serial port output 
 
  #Poll the OS for the specifically the Imax.
  while True:
    #Found from above methods or from Wireshark usb output  
    dev = usb.core.find(idVendor=0x0000, idProduct=0x0001)
    if not dev is None:
      break
    else:
     print('Device not found. Waiting for device to be connected, or hit Ctrl-C to quit.')
    time.sleep(2)
    
  print('Decimal VendorID=' + hex(dev.idVendor) + ' & ProductID=' + hex(dev.idProduct) + '\n')

  try:
    # Linux support, detach kernel driver if used
    if dev.is_kernel_driver_active(0):
      try:
        dev.detach_kernel_driver(0)
        print("Kernel driver detached")
      except usb.USBError as e:
        raise IOError("Could not detach kernel driver") from e
    else:
      print("No kernel driver attached")
  except NotImplementedError as e:
    print(f"Not implemented: '{e}', proceeding")

  #Confirm device is IMAX
  if dev:
    print('device found: ', dev)
    print('Decimal VendorID=' + str(dev.idVendor) + ' & ProductID=' + str(dev.idProduct) + '\n')
    print('Hexadecimal VendorID=' + hex(dev.idVendor) + ' & ProductID=' + hex(dev.idProduct) + '\n\n') 
    try:
      manuf = usb.util.get_string(dev, dev.iManufacturer)
      if manuf: print('manufacturer is: ', manuf)    
    except:
      pass
    try:
      serno = usb.util.get_string(dev, dev.iSerialNumber)
      if serno: print('serial num is: ', serno)
    except:
      pass
  else:
    raise ValueError('Device not found')

  # set the active configuration. With no arguments, the first configuration will be the active one
  print('Getting config')  
  dev.set_configuration()
  print('Getting active configuration.')
  cfg = dev.get_active_configuration()
  print('Got active Cfg')
  print('Attempting to get default interface')
  intf = cfg[(0,0)]
  #AN ENDPOINT IS A BYTE BUCKET TO SEND OR RECEIVE DATA
  # match the first OUT endpoint
  #from the pyusb example:
  #find the two endpoints; actually find endpoint attributes group; read and write take all the info under the ENDPOINT attributes group
  ep_out = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
  ep_in = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)    

  assert ep_out is not None
  assert ep_in is not None
  #print('ep out is:', ep_out) #should be 0x1 + all Endpoint_out attributes
  #print('ep in is:', ep_in) #should be 0x81 + all other Endpoint_in attributes
  
  """
  #For changing and initiating conditions via python
  #Generate the packets to output to the IMAX B6 Mini device. According to the Wireshack data,
  #the packet size for in and out is 64 bytes to set up and collect data.
  #Data out (host->imax) byte sequences below were obtained from WireShark USBPcap interrupt ENDPOINT_0UT
  #The setup sequence consists of 11, 64 byte packets sent from the host to IMAX before querying for run data. 
  #The first 10 INTERRUPT_OUT set up packets only change in the first 5 bytes of the 64 byte packets, 
  #followed by an eleventh packet with many more byte changes.
  #WireSharks' "Leftover Capture Data" sequences,with only a subset consisting of first 7 bytes.
  out_setup = [[0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff],
               [0x0f, 0x03, 0x57, 0x00, 0x57, 0xff, 0xff],
               [0x0f, 0x03, 0x57, 0x00, 0x57, 0xff, 0xff],
               [0x0f, 0x03, 0x5f, 0x00, 0x5f, 0xff, 0xff],
               [0x0f, 0x03, 0xfe, 0x00, 0xfe, 0xff, 0xff],
               [0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff],
               [0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff],
               [0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff],
               [0x0f, 0x03, 0x5f, 0x00, 0x5f, 0xff, 0xff]]
               
  #WARNING! THE NEXT PACKET SEQUENCE CHANGES THE IMAX SETTINGS
  SET UP PACKET BYTES (VAR: final_setup_out)  SEE DOCUMENTATION FOR DETAILS.
  #This example worked, despite the issue that byte 23 was not correctly calculated.
  #It has been superceded by a full understanding of the host byte packet sent, which 
  #are not calculated in this module. See run_imax.py for details on how the settings 
  #packet is really generated, consistent with desired battery options.
  final_setup_out = [0x0f, 0x16, 0x05, 0x00, 0x04, 0x08, 0x00, 0x01, 0xf4, 0x01, 0x2c, 
                    0x04, 0x4c, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x87, 0xff, 0xff]
               
  #generate and send the 10, 64 byte output setup sequences that the imax expects
  for b in out_setup:
    b_64 = b + [0]*57
    time.sleep(0.1)
    w_out = dev.write(ep_out, b_64)
    data = dev.read(ep_in, 64) # if using in_buff
    #print(data) #used for testing
  #send final eleventh non repeating sequence out to device
  final_setup_out_64 = final_setup_out + [0]*57
  w_out = dev.write(ep_out, final_setup_out_64)
  data = dev.read(ep_in, 64)
  #print(data) #used for testing

  #Finally, create the host->IMAX Interrupt packet. This is the aame as Milek7 shows.
  #e.g.
  data_out_packet =[
             0x0F, 0x03, 0x55, 0x00, 0x55, 0xFF, 0xFF, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
           ]
  """
  #condensed form of packets
  data_out_packet = [0x0f, 0x03, 0x55, 0x00, 0x55, 0xff, 0xff] + [0]*57 
  imax_settings_out =[0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff] + [0]*57
  #get limits, cycle delay (and buzzer status (last not called out.
  w_out = dev.write(ep_out, imax_settings_out)
  idle_settings = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize)  
  data_run = []
  if idle_settings:
    w_out = dev.write(ep_out, imax_settings_out)
    imax_sys_settings = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize)
    cycle_delay = str(imax_sys_settings[5]) #in min
    max_chrg_time = str(imax_sys_settings[7]*256 + imax_sys_settings[8]) #in min
    max_mv = str(imax_sys_settings[10]*256 + imax_sys_settings[11]) #in mV
    max_input_V = str((imax_sys_settings[14]*256 + imax_sys_settings[15])/1000) #in V
    print('Settings: Max Charge(mah): ' + max_chrg_time + ' min; mV(max): ' + max_input_V +' V; ' + 'Cycle delay: ' + cycle_delay + ' min.')
    
  #for some reason Chargemaster sends 3 packets in quick succession; so me too....
  for i in range(3):
    w_out = dev.write(ep_out, data_out_packet)      

  t = time.perf_counter()

  #alternate wrtie packet method -faster, if needed?
  #import array
  #in_buff = array.array('B', [0])
  #w_out = dev.write(ep_out, data_out_packet) 
  w_out = dev.write(ep_out, data_out_packet) 
  try:
    data = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize) #using more general form of Endpoint_IN attributes 
  except Exception as e: 
    print('Something went wrong: error is: ', e)
  #header for console output
  print ("state, energy, timer, voltage, current, ext temp, int temp, cell 1, cell 2, cell 3, cell 4, cell 5, cell 6")  
  #cycle until run condition met
  while True:
    #check if device still available
    if not dev:
      print('Device no longer available...aborting.')
      break
    old_data = str(data[5] * 256 + data[6])
    #send the host->imax packet to trigger imax to fill buffer and do imax->host transfer
    w_out = dev.write(ep_out, data_out_packet)    
    try:
      data = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize) #using more general form of Endpoint_IN attributes 
    except Exception as e: 
      print('Something went wrong: error is: ', e) 
   #print the data; this is same sequence that Milek7 used with hidapi; much appreciated effort.
    print(
      str(data[4]) + ", " +                                 #state
      str(data[5] * 256 + data[6]) + ", " +                 #energy
      str(data[7] * 256 + data[8]) + ", " +                 #timer     
      str((data[9] * 256 + data[10]) / 1000.0) + ", " +     #voltage
      str((data[11] * 256 + data[12]) / 1000.0) + ", " +    #current
      str(data[13]) + ", " +                                #ext temp
      str(data[14]) + ", " +                                #int temp
      str((data[17] * 256 + data[18]) / 1000.0) + ", " +    #cell 1    
      str((data[19] * 256 + data[20]) / 1000.0) + ", " +    #cels 2
      str((data[21] * 256 + data[22]) / 1000.0) + ", " +    #cell 3
      str((data[23] * 256 + data[24]) / 1000.0) + ", " +    #cell 4
      str((data[25] * 256 + data[26]) / 1000.0) + ", " +    #cell 5
      str((data[27] * 256 + data[28]) / 1000.0)             #cell 6
    )
    #append raw data byte packet data to running list of output points
    data_run.append(data)
    sys.stdout.flush()
    #check status; 1 = IMAX running; 2 = user stop (btn pressed); 3 = normal stop
    if str(data[4]) > str(1): #2 = user stop; 3 = imax finished.
      final_out = [0x0f,	0x03, 0xfe,	0x000, 0xfe, 0xff, 0xff] + [0]*57
      w_out = dev.write(ep_out, final_out)
      final_data = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize)
      w_out = dev.write(ep_out, imax_settings_out)
      final_settings = dev.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize)
      break #this will set while to false; we are finished. 

    #To create smoother plots and to keep output data to reasonable size
    #thought about using a variable time interval based on derivative of 
    #voltage and/or capacity, probably based on voltage, but decided more 
    #trouble than useful.
    
    time.sleep(query_interval - (time.perf_counter() - t))
    t = time.perf_counter()
    
  #generate the final run totals
  if final_out:
    final_mah = str(data[5] * 256 + data[6])            #energy
    final_t = str(data[7] * 256 + data[8])              #timer    sec 
    final_V = str((data[9] * 256 + data[10]) / 1000.0)  #voltage, V
    final_T = str(data[14])                              #Temperature, deg C, if F???
    #int temp 
  final_dict = {'final_mah':final_mah, 'final_time':final_t, 'final_V':final_V, 'final_T':final_T}
  # set the settings dictionary
  if idle_settings: 
    settings_dict = { 'cycle_delay':cycle_delay, 'max_chrg_time':max_chrg_time, 'max_mv':max_mv, max_input_V:max_input_V}
    
  #do we want to use json?  
  #setting_json = json.dumps(settings_dict})
  # load to dict
  #my_dict = json.loads(settings_json)                       
  
  #convert the byte data list to more readable output
  if data_run:
    for r in data_run:
      a_row = [str(r[5] * 256 + r[6]),               #energy
              str(r[7] * 256 + r[8]),                #timer     
              str((r[9] * 256 + r[10]) / 1000.0),    #voltage
              str((r[11] * 256 + r[12]) / 1000.0),   #current
              str(r[13]),                            #ext temp
              str(r[14]),                            #int temp
              str((r[17] * 256 + r[18]) / 1000.0),   #cell 1    
              str((r[19] * 256 + r[20]) / 1000.0),   #cels 2
              str((r[21] * 256 + r[22]) / 1000.0),   #cell 3
              str((r[23] * 256 + r[24]) / 1000.0),   #cell 4
              str((r[25] * 256 + r[26]) / 1000.0),   #cell 5
              str((r[27] * 256 + r[28]) / 1000.0)]   #cell 6
      data_out.append(a_row)
      data_out_dict = {'data':data_out}
      
  #simple storage    
  output_csv(header, data_out, final_dict)


def __main__():
  #uncomment next line to find all hids (human interface devices)
  #Prints all hid to cmd or Powershell console.
  #find_hids()
  
  #uncomment 'find_our_device()' line to find all hids (human interface devices)
  #by running the below method with ahd without the device connected,
  #should be able to zero in on new device.
  #WireShark may be a better way to fimd the data though.
  #find_our_device will print details of ALL devices, which may be huge list.
  #Depending on how cmd console set up, many devices may scroll off.
  #find_our_device()

  #start the imax reader
  imax = start_imax()
  if not imax:
    print("data recording stopped")


if __name__== "__main__":
  __main__()
