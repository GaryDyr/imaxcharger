
#Lists all the devices on a system; it does not descriminate by type of device, e.g., Human Interface Devices (hid)
#Requires hidapi be installed.
#Download the system compatible hidapi .whl file and do (for example:
#pip install hidapi-0.7.99.post21-cp36-cp36m-win_amd64.whl
import hid
import os
import sys
import csv

#found this code on internet and added here with a slight modification.
def list_devices():
  devices = []
  #grd hid.enumerate(0,0) generates a linked list of all devices  
  for d in hid.enumerate(0, 0):
    keys = d.keys() 
    #keys.sort() 
    for key in keys: 
      print( "%s : %s" % (key, d[key])) 
      devices.append((key,d[key]))

  cur_dir = os.getcwd()
  csv_file = 'devices.csv'
  #Best way to get the current path of the module and file
  list_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_file)

  # check if path and old event file exist; if not create it
  if os.path.isfile(list_file):
    #create the file and populate first time, we know data exists
    print('creating new list')
    with open(list_file,"w", encoding='utf-8')  as f:
      writer=csv.writer(f, delimiter=",", lineterminator="\r\n") 
      writer.writerows(devices)

   return devices

list_devices()
