


# https://github.com/Milek7/imax-b6mini-datalogger
#MIGHT B E LESS HASSLE GETTING HIDAPI, EVEN THOUGH ARE DEPENDENT ON WHL
# Requires hidapi; get here: https://pypi.python.org/pypi/hidapi/0.7.99.post21

#THE BELOW USES THE HIDAPI RATHER THAN PYUSB FOR THE MINI
#MAY BE ABLE TO DIRECTLY READ THE DEVICE NAME, VENDER_ID AND PRODUCT_ID IN WINDOWS DEVICE MANAGER:
#CONNECT DEVICE TO USB PORT, WHEN IT INDICATES INSTALLED, GO TO DEVICE MANAGER|EVENTS. THERE WILL BE
#THE 4 HEXADECIMAL DATA FOR VENDER_ID, PRODUCT_ID AND DETAILED PATH THAT WINDOWS SUPPLIES.


#!/usr/bin/env python3
import time
import hid
import sys


#???????????????????????
#these may not make any sense and need to be changed to following once vendor_id and 
#config

#MUST GET THE PROPER HEXADECIMAL VALUES HERE: (VENDOR_ID, PRODUCT_ID)

device = (0x000, 0x0001)
###

h = hid.device()
h.open(device[0], device[1])
#GRD ADDED
res = h.get_manufacturer_string()
print('Device name is: ', res)
print("Product: %s" % h.get_product_string())  
print("Serial No: %s" % h.get_serial_number_string())
#GRD THIS APPARENTLY is dumping, or clearing stuff.
#write sends controls, triggers, data object, 
#Using logview with a device monitor as soon as you click on the 
#device checkbox, the sequence below shows up. Why send this 64 bytes?
#does this set up what to read back.
#h.set_nonblocking(1)  


"""
original
inw = h.write([
0x0F, 0x03, 0x55, 0x00, 0x55, 0xFF, 0xFF, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00])

"""
inw = [
0x0F, 0x03, 0x5A, 0x00, 0x5A, 0xFF, 0xFF, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00]

#can be written as 
#h.write([0x0F, 0x03, 0x5A, 0x00, 0x5A, 0xFF, 0xFF] + [0]*57)
h.read(64,1000)
print ("state, energy, timer, voltage, current, ext temp, int temp, cell 1, cell 2, cell 3, cell 4, cell 5, cell 6")
#original code used time.clock(), but clock is deprecated as of 3.3
t = time.perf_counter()
query_interval = 5
while True:
  #out_stuff = h.write(inw) #this is a typical trigger
  #time.sleep(0.05)
  #original trigger
  #h.write([0]) #with the original nothing comes back Milek7 did not try with windows but 'thought' it would work 
  data = h.read(64,1000) #should be able to use without adding 1000, but it hangs.
  if data:
    print(data)
   #if (len(data) < 29):
    #	print("err")
   #	continue
    #This is the correct output relationship
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
      str((data[27] * 256 + data[28]) / 1000.0)            #cell 6
    )
  else:
    print('nothing came back')
    #sys.exit()
  sys.stdout.flush()
  time.sleep(query_interval - (time.perf_counter() - t))
  t = time.perf_counter()

