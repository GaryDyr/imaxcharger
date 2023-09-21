#
"""
Copyright © 2018, Gary Dyrkdacz <gdyrkacz@gmail.com> 
 
Permission to use, copy, modify, and/or distribute this software for any 
purpose with or without fee is hereby granted,  provided that the above 
copyright notice and this permission notice appear in all copies. 
 
THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES 
WITH  REGARD  TO  THIS  SOFTWARE  INCLUDING  ALL  IMPLIED  WARRANTIES OF 
MERCHANTABILITY AND FITNESS.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR 
ANY SPECIAL,  DIRECT,  INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
WHATSOEVER RESULTING  FROM LOSS OF USE,  DATA OR PROFITS,  WHETHER IN AN 
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF 
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. 
"""
#Application using default browser to open dashboard to control an Imax B6 Mini Charger.
#Tested and run under Windows 10 2018 Spring Revision 1903, with Python 3.6.3, bokeh 12.16
##Before starting the module, make sure you have installed all the external modules: 
#   bokeh
#   pyusb,
#  SQLalchemy 
#The first two packages require other python packages or libraries be installed first.  
#See the installation instructions of each package for details.
#Start this module with:
#  bokeh serve --show select_test.py 

import os
import sys
import time
import datetime
import configparser
from bokeh.models import DataTable, TableColumn
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.io import output_file, show
from bokeh.layouts import column, row
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider, RadioGroup,Div, TextInput
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import gridplot, layout
from bokeh.plotting import curdoc 
from bokeh.driving import linear
from bokeh.models.callbacks import CustomJS
import random
import db_ops
from db_ops import session, Programs
#-----------------INITIALIZE SETTINGS----------------------------------------------------------
#get the default battery type from the config file, currently = NiMH)
#see imaxconfig.ini to change

#Logic: The battery type is the most critical element to structure all
#other parameters. Key off of that as much as possible.
#USER MUST INPUT bat_type, nominal_mah, cells,

config_file = 'imaxconfig.ini'
settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
config = configparser.ConfigParser()
config.read(settings_file)

bat_type = config['BatterySettings']['bat_type'] #set default to NiMH
cells = int(config['BatterySettings']['cells']) # set default to 1
slider_max = int(config['SelectorSettings']['slider_max'])
nominal_mah_start = int(config['SelectorSettings']['nominal_mah_start'])
#bat_type = "NiMH"
#initialize varibles for inputs.
chrg_type = "Charge"
#nominal_mah = 100
nominal_mah = nominal_mah_start
DC_or_CD = 0 #Discharge/Charge"
cycles = 1
safe_C = 400
safe_D = 300
chrg_rate = 100
dchrg_rate= 100
battery_use = ""
prgm_id = None
id_list = []
prgm_list = []
prgm_index = []
run_text = ""
max_charge_time = 180
run_status = 0
run_text = "Enter run information"
time_interval = 10 #seconds
final_read = {'final_mah':"", 'final_t':"", 'final_V':"", 'final_T':""}
#next is set in start_device(), which is obtained from imax.start_imax
device_dict = {'device':None, 'EndPt_out':None, 'EndPt_in':None}
text_update = None 
settings_dict = {}
read_data = {}
data_out_packet = []
device_started = False
out_data = {}
start_cycle = None
cycle_delay = 3
run_status = 0
settings_packet = []
battery_use = 'Enter short battery use info.'

#used for cycling time fix
base_time = 0
old_time = 0

#slider_max = 24050
#used by delete method to reset conditions
reset_settings = {'bat_type':config['BatterySettings']['bat_type'],
                  'cells':int(config['BatterySettings']['cells']), 
                  'slider_max':int(config['SelectorSettings']['slider_max']),
                  'nominal_mah_start':int(config['SelectorSettings']['nominal_mah_start']),
                  'chrg_type':"Charge",
                  'nominal_mah':nominal_mah_start,
                  'DC_or_CD':0,
                  'cycles':str(1),
                  'cells':str(1),
                  'safe_C':str(400),
                  'safe_D':str(300),
                  'chrg_rate':str(100),
                  'dchrg_rate':str(100),
                  'battery_use':"Enter short battery use info",
                  'prgm_id':None,
                  'id_list':[],
                  'prgm_list':[],
                  'prgm_index':[],
                  'run_text':"Enter run information",
                  'max_charge_time':str(180),
                  'start_cycle':None,
                  'cycle_delay':3,
                  'run_status':0,
                  'set_prgm':0}


notice1 = Div(text="""The data input here are for logging identification and saving conditions, which are already manually chosen 
                on the imax. They do not set or reset the imax.""",
                sizing_mode = "scale_width")
settings_dict = {'max_charge_time':"", 'max_input_V':"", 'cycle_delay':""}


# text to byte value conversions
# all values based on settings analysis; see documentation
btype = {'LiPO':0x00, 'LiION':0x01, 'LiFe':0x02, 'LiHV':0x03, 'NiMH':0x04, 'NiCd':0x05, 'Pb':0x06}                         #byte 4
NiXX_CD_Modes ={"Charge":0x00, "AutoCharge":0x01, "Discharge":0x02, "Re-Peak":0x03, "Cycle":0x04}                #byte 6
LiXX_CD_Modes = {"Charge":0x00, "Discharge":0x01, "Storage":0x02, "Fast Charge":0x03, "Balance Charge":0x04} #byte 6
Pb_CD_Modes = {"Charge":0x00, "Discharge":0x01}

#sensitivities based on either settable sensitivity or for LiXX uses maxV
sensitivity = {'NiMH':0x0004, 'NiCd':0x0004, 'LiPO':0x1068, 'LiFe':0x0e74, 'LiHV':0x10fe, 'LiION':0x0e10, 'Pb':0x0000} #bytes 13 & 14
DC_CD = {0:0x00, 1:0x01} 
safe_C_frac = {'NiMH':0.40, 'NiCd':0.40, 'LiPO':0.50, 'LiFe':1.0, 'LiION':0.50, 'LiHV':0.50, 'Pb':0.30}
cells_rng = {'NiMH':13, 'NiCd':13, 'LiPO':13, 'LiFe':13, 'LiION':13, 'LiHV':13, 'Pb':7}  

#Master lis of Imax supported battery types
bat_types =  ['NiMH', 'NiCd', 'LiPO', 'LiFe', 'LiION', 'LiHV', 'Pb']
#Charge options vary by battery type.
generic_chrg = ["Charge", "Cycle", "Re-Peak", "AutoCharge", "Balance Charge", "Fast Charge", "Storage"] 
NiXX_options =["Charge", "Discharge", "Cycle", "Re-Peak", "AutoCharge"] 
LiXX_options = ["Charge", "Discharge", "Balance Charge", "Fast Charge", "Storage"]
Pb_options = ["Charge", "Discharge"]

#generate master lis of all selectable widgets
sel_type = ['bat','chrg', 'dchrg', 'slider', 'cells' 'rad', 'chrg_rate', 'dchrg_rate', 'minV', 'DCrad']

#limits dictionary with lists with values in order (taken from Imax B6 mine manual: 
#[NomV/Cell, MaxChrgV/Cell, StorV/Cell, AllowableFastChrg, MinDischrgV/Cell]
limits = {'LiPO': [3700, 4200, 3800, 1,      [3000, 3300]], 
          'LiION':[3600, 4100, 3700, 1,      [2900, 3200]], 
          'LiFe': [3300, 3600, 3300, 4,      [2600, 2900]],
          'LiHV': [3700, 4200, 3800, 1,      [3000, 3300]],          
          'NiCd': [1200, 1500, None, [1, 2], [100, 1100]],
          'NiMH': [1200, 1500, None, [1, 2], [100, 1100]],
          'Pb':   [2000, 2460, None, 0.4,     1800]}
      
#set options lists 
chrglist = [str(i) for i in range(100, 1100, 100)]
dchrglist = [str(i) for i in range(100,2100, 100)]
minV = limits[bat_type][4][1] #Not lowest, but conservative value for most cells
minV_rng = [str(i) for i in range(limits[bat_type][4][0],limits[bat_type][4][1] + 100, 100)]

maxV = limits[bat_type][1]          
#Logic: The battery type is the most critical element to structure all
#other parameters. Key off of that because it is the only locked set of options.
#batery type drives many other parameters.

#Generte a master dictionary of various setttings. As a dictionary, it represents
#a global way to store information in entire module
settings = {
              'bat_type':bat_type, 
              'cells':str(cells), 
              'chrg_type':chrg_type, 
              'nominal_mah':str(nominal_mah), 
              'DC_or_CD':DC_or_CD, 
              'cycles':str(cycles), 
              'safe_C':str(safe_C), 
              'safe_D':str(safe_D), 
              'chrg_rate':str(chrg_rate), 
              'chrglist':chrglist,
              'dchrg_rate':str(dchrg_rate), 
              'dchrglist':dchrglist, 
              'maxV':str(maxV), 
              'minV':str(minV), 
              'minV_rng':minV_rng, 
              'max_charge_time':str(max_charge_time), 
              'battery_use':battery_use, 
              'prgm_id':prgm_id, 
              'prgmn_list':prgm_list, 
              'prgm_index':prgm_index, 
              'id_list':id_list,
              'device_started':device_started,
              'time_interval':time_interval,
              'start_cycle':start_cycle,
              'cycle_delay':cycle_delay,
              'run_text':run_text,
              'run_status':run_status,
              'final_out':final_read,
              'data_out_packet':data_out_packet,
              'settings_dict':settings_dict,
              'device_dict':device_dict,
              'set_prgm':0
           }
        
#----------------END INITIALIZE SETTINGS----------------------------------------------------

def get_settings_packet():
  #Builds the 64 bit settings packet as list to send to the imax
  global settings_packet
  #Build individual bytes
  byte0 = (0x0f).to_bytes(1, 'big')
  byte1 = (0x16).to_bytes(1, 'big')
  byte2 = (0x05).to_bytes(1, 'big')
  byte3 = (0x00).to_bytes(1, 'big')
  byte4 = btype[settings['bat_type']].to_bytes(1 , 'big')         # battery type
  byte5 = int(settings['cells']).to_bytes(1, 'big')               # No. of cells
  #byte 6 is charge type
  if 'Li' in settings['bat_type']: byte6 = LiXX_CD_Modes[settings['chrg_type']].to_bytes(1 , 'big')
  if 'Ni' in settings['bat_type']: byte6 = NiXX_CD_Modes[settings['chrg_type']].to_bytes(1, 'big')
  if settings['bat_type'] == 'Pb': byte6 = Pb_CD_Modes[settings['chrg_type']].to_bytes(1, 'big')
  #get mah charge/discharge rate; 2 bytes
  abyte = int(settings['chrg_rate']).to_bytes(2, 'big')
  byte7 = abyte[:1]
  byte8 = abyte[-1:]
  #get mah discharge rate; 2 bytes
  abyte = int(settings['dchrg_rate']).to_bytes(2, 'big')
  byte9 = abyte[:1]
  byte10 = abyte[-1:]
  #get minimum voltage; 2 bytes
  abyte = int(settings['minV']).to_bytes(2, 'big')
  byte11 = abyte[:1]
  byte12 = abyte[-1:] 
  #get sensitivities imax uses for knowing when to stop runs; 2 bytes
  abyte = sensitivity[settings['bat_type']].to_bytes(2, 'big')
  byte13 = abyte[:1]
  byte14 = abyte[-1:]
  #get byte for charge/discharge or discharge/charge   
  byte15 = DC_CD[int(settings['DC_or_CD'])].to_bytes(1,'big')
  #get byte for number of CD/DC cycles 
  byte16 = int(settings['cycles']).to_bytes(1, 'big')
  #Build the initial settings packet of byte values
  settings_packet = [byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7,
                     byte8, byte9, byte10, byte11, byte12, byte13, byte14, byte15,
                     byte16]
  #Add in the static bytes values to byte 23
  xbytelist = [(0).to_bytes(1, 'big')]*7 + [(0xff).to_bytes(1, 'big')]*2
  settings_packet = settings_packet + xbytelist 
  #byte23 is the low order byte from sum of bytes 2->23
  #add bytes 2 to 23 (first convert to integers; convert to byte string; get lowest byte
  sm = 0
  for i in range(2, 22):
    #convert each byte to integer and add; from_bytes requires str
    sm = sm + int.from_bytes(settings_packet[i], byteorder = 'big')
  #get lowest order byte
  settings_packet[23] = sm.to_bytes(8, 'little')[:1]
  #complete 64 byte packet; add static bytes from 24 to 64
  settings_packet = settings_packet + [(0).to_bytes(1, 'big')]*38
  settings_packet = b''.join(settings_packet)
  #print(settings_packet)
  print('finished getting packet')
  return settings_packet

def update_selects(b_type, sel_type):
  #Updates dependent widget parameters for both non program selector changes and program driven selector changes
  #b_type = battery type; sel_type = selector changed or clicked
  #Explicitly called from select handlers, but for programs implicitly called from prgm_set() method
  #prgm_set() uses settings['set_prgm'] to control if user setting values (0) or prgm being recalled (1) 
  #Order of changing values is important, becasue of dependencies of varous pramaters
  #good news is changing value and options is sufficient.
  #bad news there are redundancies for certain calls  
  #print('in u_s')
  #Is user updating individual widgets, and not a program?
  #settings['set_prgm'] is set and reset in prgm_set(), which in turn is called by select_prgm_handler
  if settings['set_prgm'] == 0: 
    print('u_s: in prgm False')
    if sel_type == 'bat': #battery type changed
      print('in u_s bat; bat type is', b_type)
      #update all ranges and values
      settings['chrglist'] = [str(i) for i in range(0, int(settings['nominal_mah']) + 100, 100)]
      select_chrg_rate.options = settings['chrglist']
      if 'Ni' in b_type:
        select_chrg_type.options = NiXX_options
        if not select_chrg_type.value in NiXX_options:
          select_chrg_type.value = 'Charge'
      elif 'Li' in b_type:
        select_chrg_type.options = LiXX_options
        if not select_chrg_type.value in LiXX_options:
          select_chrg_type.value = 'Charge'
      elif b_type == 'Pb':
        select_chrg_type.options = Pb_options
        if not select_chrg_type.value in Pb_options:
           select_chrg_type.value = 'Charge' 
      #get safe_C from safe C values dict defined at top of module
      safe_C = str(round((safe_C_frac[b_type]*int(settings['nominal_mah']))/100)*100)      
      print('in bat: safe C is: ', safe_C, ' of type ', type(safe_C))
      settings['chrg_rate'] = safe_C
      settings['safe_C'] = safe_C
      select_chrg_rate.value = safe_C
      print('bat reports chrg_rate value set to: ', safe_C)
      if b_type != 'Pb':      
        settings['minV'] = str(limits[b_type][4][1])
        settings['minV_rng'] = [str(i) for i in range(limits[b_type][4][0], limits[b_type][4][1]+100, 100)]
        #also update cells options
      else: #is Pb
        settings['minV'] = str(limits[b_type][4])
        settings['minV_rng'] = [str(limits[b_type][4])]
      select_cells.options = [str(i) for i in range(1, cells_rng[b_type])]  
      print('in bat, minV is: ', minV)
      select_minV.options = settings['minV_rng']     
      settings['maxV'] = str(limits[b_type][1]) #per cell
      select_minV.value = settings['minV']
      print('leaving u_s bat')
    #Deal with slider change; affects charge rate (mA)
    #User may have already changed chrg_rate first, just watch for outside allowed range  
    if  sel_type == 'slider': #returns a float
      print('in u_s slider')
      if int(settings['nominal_mah']) >= 100:
        safe_C = str(round((safe_C_frac[b_type]*int(settings['nominal_mah']))/100)*100)
        settings['safe_C'] = safe_C
        #User may have set chrg rate before changing capacity
        #only get involved if chrg_rate exceeds bat capacity/cell
        select_chrg_rate.value = settings['safe_C']        
        if int(settings['chrg_rate']) > limits[b_type][0]:
          #slider returns mah at 50 mA intervals
          # only allow masimum of of 1C rates as maximum    
          #print('new_rate: ', select_chrg_rate.value)
          settings['chrg_rate'] = settings['safe_C']
        settings['chrglist'] = [str(i) for i in range(0, int(settings['nominal_mah']) + 100, 100)]
        select_chrg_rate.options = settings['chrglist'] 
        if b_type == "Pb":
          settings['safe_C'] = str(round((0.3*int(settings['nominal_mah']))/100)*100)
          settings['chrglist'] = [str(i) for i in range(0, int(settings['nominal_mah']) + 100, 100)]
        #lock safe discharge at 300 mah; sort of mimics max draw on receiver pack
        safe_D = str(300)
        settings['dchrglist'] = [str(i) for i in range(100, 2000, 100)] #same as Imax 
        select_dchrg_rate.options = settings['dchrglist']
        print('leaving us_slider')
    if  sel_type == "cells":
      #all but Pb have same range; see dict at top
      select_cells.options = [str(i) for i in range(1,cells_rng[bat_type])]
    if sel_type == 'chrg':
      print('u_s in chrg')
      if 'Ni' in b_type:
        select_chrg_type.options = NiXX_options
        if not select_chrg_type.value in NiXX_options:
          select.chrg_type.value = 'Charge'
      if 'Li' in b_type:
        select_chrg_type.options = LiXX_options
        if not select_chrg_type.value in LiXX_options:
          select_chrg_type.value = 'Charge'
      if b_type == 'Pb':
        select.crhg_type.options = Pb_options
    if sel_type == 'minV':
      print('in u_s minV')
      if b_type in limits:
        #lock the max chrg rate
        if settings['chrg_type'] in generic_chrg: #cover all chrg options
          print(int(settings['cells']), settings['cells'], limits[b_type], limits[b_type][1])
          settings['maxV'] = str(limits[b_type][1]) #get list from dict, get 2nd max element
          if b_type != 'Pb':
            settings['minV_rng'] = [str(i) for i in range(limits[b_type][4][0],limits[b_type][4][1] + 100, 100)]
          else: #is Pb
            settings['min_V'] = str(limits[b_type][4])
            settings['minV_rng'] = [str(limits[b_type][4])]
        else: #chrg type must be discharge, go with safest value, but give range choice
          settings['minV'] = str(limits[b_type][4][1])
          settings['minV_rng'] = [str(i) for i in range(limits[b_type][4][0],limits[b_type][4][1] + 100, 100)] 
          select_minV.value = settings['minV']
          select_minV.options = settings['minV_rng']
          print('minV is: ', settings['minV'])
    if sel_type == 'chrg_rate':
      print('chrg_rate is:',settings['chrg_rate'])
      settings['chrglist'] = [str(i) for i in range(0, int(settings['nominal_mah']) + 60, 100)]
      select_chrg_rate.options = settings['chrglist']
    if sel_type == 'dchrg_rate':
     pass      
    get_settings_packet()
    print('out of u_s')
  #BELOW - DEAL WITH SETTINGS DICTATED BY PROGRAM DRIVING CHANGES; SEE PRGM_SET()
  else:
    print('u_s: in prgm True') 
    if sel_type == 'bat': #battery type changed
      print('in u_s bat; b_type is ', b_type)
      #update all ranges and values
      settings['chrglist'] = [str(i) for i in range(0, int(settings['nominal_mah']) + 100, 100)]
      select_chrg_rate.options = settings['chrglist']
      safe_C = str(round((safe_C_frac[b_type]*int(settings['nominal_mah']))/100)*100)
      if 'Ni' in b_type:
        select_chrg_type.options = NiXX_options
      if 'Li' in b_type:
        select_chrg_type.options = LiXX_options
      if b_type == 'Pb':
        select_chrg_type.options = Pb_options
      print('in bat: safe C is: ', safe_C, ' of type ', type(safe_C))
      print('prgm 1 reports chrg_rate value set to: ', settings['chrg_rate'])
      #if user has programmeddifferent value, test and fix
      settings['safe_C'] = safe_C
      if b_type != 'Pb':
        settings['minV_rng'] = [str(i) for i in range(limits[b_type][4][0],limits[b_type][4][1] + 100, 100)]
        select_minV.options = settings['minV_rng']
        select_cells.options = [str(i) for i in range(1,cells_rng[b_type])]
      else: #is Pb
        settings['minV_rng'] = [str(limits[b_type][4])] 
      select_minV.options = settings['minV_rng']
      settings['maxV'] = str(limits[b_type][1]) #per cell
      print('leaving u_s bat')
    #Deal with slider change; affects charge rate (mA)
    #User may have already changed chrg_rate first, so just watch for outside allowed range  
    if  sel_type == 'slider': #returns a float
      print('in prgm 1 u_s slider')
      if int(settings['nominal_mah']) >= 100:  
        safe_C = str(round((safe_C_frac[b_type]*int(settings['nominal_mah']))/100)*100)
        print('pgm True; in slider: safe_C is: ', safe_C)
        settings['safe_C'] = safe_C
        print('pgrm 1 reports chrg_rate: ', settings['chrg_rate'])
        if int(settings['chrg_rate']) > limits[b_type][0]:
          print('new_rate: ', select_chrg_rate.value)
        settings['chrglist'] = [str(i) for i in range(100, int(settings['nominal_mah']) + 100, 100)]
        select_chrg_rate.options = settings['chrglist']        
        safe_D = str(300)  
        settings['dchrglist'] = [str(i) for i in range(100, 2000, 100)] #same as Imax 
        select_dchrg_rate.options = settings['dchrglist']
        print('leaving us_slider')
    if sel_type == "cells":
      print('in u_s pgm True; cells') 
      #Pb has different range, so check reset        
      select_cells.options = [str(i) for i in range(1, cells_rng[b_type])]
    #if sel_type == "cycles":
       #print('in u_s prm 1 cycles:', settings['cycles']) 
    if sel_type == 'minV':
      print('minV value is: ', select_minV.value)
      if b_type in limits:
        #lock the max chrg rate
        if settings['chrg_type'] in generic_chrg: #cover all chrg options
          settings['maxV'] = str(limits[b_type][1]) #get list from dict, get 2nd max element
          print('maxV is: ', settings['maxV'])
        else: #must be discharge option, 
          if b_type != 'Pb':
            settings['minV_rng'] = [str(i) for i in range(limits[b_type][4][0],limits[b_type][4][1] + 100, 100)] 
            select_minV.options = settings['minV_rng']
          else:
            settings['minV_rng'] = [str(limits[b_type][4])]
            select_minV.options = settings['minV_rng']          
        print('prgm 1 minV is: ', settings['minV'])
    if sel_type == 'chrg_rate':
      print('in u_s prgm 1 chrg_rate')
      settings['chrglist'] = [str(i) for i in range(100, int(settings['nominal_mah'])+100, 100)]
      select_chrg_rate.options = settings['chrglist']
    if sel_type == 'dchrg_rate':
      print('in us_s prgm 1, dchrg is:' , dchrg_rate)
      #options are locked to 0 to 2 Amps
      pass
    get_settings_packet()
    print('out of u_s')    
  
#-------------Create Widgets and Handlers---------------------------------------------------------      
#Note issue with selects. They only have a ON_CHANGE event. Therefore, cannot pick same
#value in list to repopulate back to an already picked value. Could not figure out a way around issue. 
 
select_chrg_type = Select(title="Charge Type", value="Charge", options= NiXX_options)
def select_chrg_type_handler(attr, old, new):
  settings['chrg_type'] = new
  print('Charge Type selected: ', new)
  update_selects(settings['bat_type'], 'chrg')
select_chrg_type.on_change('value', select_chrg_type_handler)
#slider_max is set in config.ini

maxmah_slider = Slider(start=200, end=slider_max, value=100, step=50, title="Bat. Specified Capacity, mah")
def maxmah_handler(attr, old, new):
  settings['nominal_mah']= new
  print('Nominal mah selected: ' + str(new))
  update_selects(settings['bat_type'], 'slider')
maxmah_slider.on_change('value', maxmah_handler)

DC_radio_group = RadioGroup(labels=["Charge/Discharge", "Discharge/Charge"], active=0)
def DC_radio_handler():
  print('inDC handler')
  settings['DC_or_CD'] = DC_radio_group.active 
  print('Radio button option ' + str(DC_radio_group.active) + ' selected.')
  #update_selects(bat_type, 'DCrad')  
DC_radio_group.on_change('active', lambda attr, old, new:DC_radio_handler())

select_cells = Select(title = "No. of Cells", value ="0", options = [str(i) for i in range(1, cells_rng[settings['bat_type']])])
def select_cells_handler(attr, old, new):
  settings['cells'] = new
  print('cells selected: ' + str(new))
  update_selects(settings['bat_type'], 'cells')
select_cells.on_change('value', select_cells_handler)

#Reminder select dropdowns only accept and return strings
select_chrg_rate = Select(title = "Charge Rate, mA", value = str(round((0.4*int(settings['nominal_mah']))/100)*100), options = settings['chrglist'])
def select_chrg_rate_handler(attr, old, new):
  settings['chrg_rate'] = new
  print('handler reports chrg_rate new is: ' + str(new))
  update_selects(settings['bat_type'], 'chrg_rate')
select_chrg_rate.on_change('value', select_chrg_rate_handler)

select_dchrg_rate = Select(title = "Discharge Rate, mA", value =str(round((0.3*int(settings['nominal_mah']))/100)*100), options = settings['dchrglist'])
def select_dchrg_rate_handler(attr, old, new):
  print('in select_dchrg')
  settings['dchrg_rate'] = new
  update_selects(settings['bat_type'], 'dchrg_rate')
select_dchrg_rate.on_change('value', select_dchrg_rate_handler)

select_battype = Select(title = "Battery Type", value ="", options = ['NiMH', 'NiCd', 'LiPO', 'LiFe', 'LiION', 'LiHV', 'Pb'])
def select_battype_handler(attr, old, new):
  settings['bat_type'] = new
  print('Battery type selected: ' + new)
  update_selects(settings['bat_type'], 'bat')
select_battype.on_change('value', select_battype_handler)

select_cycles = Select(title = "Cycles", value ="1", options = [str(i) for i in range(0,6)])
def select_cycles_handler(attr, old, new):
  print('in cycles')
  settings['cycles'] = new
  if 'Ni' in settings['bat_type'] and settings['chrg_type'] == 'Cycle': 
    if int(settings['cycles']) > 0:
      settings['cycles'] = new
  else:
    settings['cycles'] = str(0)
  print('cycles selected: ' + new)
  #update_selects(settings['bat_type'], 'cycles')
select_cycles.on_change('value', select_cycles_handler)

select_minV = Select(title = "Minimum Discarge Voltage/Cell, mV", value = settings['minV'], options =settings['minV_rng'])
def select_minV_handler(attr, old, new):
  settings['minV'] = new
  print('minV selected: ' + new)
  update_selects(settings['bat_type'], 'minV')
select_minV.on_change('value', select_minV_handler)

text_input = TextInput(value="Enter run information", title="Run Information:")
def text_input_handler(attr, old, new):
  settings['run_text'] = new
  print("Updated label: " + new)
text_input.on_change("value", text_input_handler)

use_input = TextInput(value="Enter short battery use info", title="Battery Usage Title:")
def use_input_handler(attr, old, new):
  if new == None or new == "":
    settings['battery_use'] = settings['bat_type'] + " type:" + settings['chrg_type'] + " rate:" + settings['chrg_rate'] + 'psuedo id:'+random.randint(1000,9000)
    print("Updated label: " + new)
  else:
    settings['battery_use'] = new
use_input.on_change("value", use_input_handler)

def prgm_set(pset):
  #called by select_prgm_handler
  #updates settings dictionary and transfers picked 
  #program settings to widget values
  print('in prgm_set')
  settings['bat_type'] = pset.battery_type
  settings['battery_use'] = pset.battery_use
  settings['nominal_mah'] = str(pset.nominal_mah)
  settings['cells'] = str(pset.battery_cells)
  settings['chrg_type'] = pset.chrg_type
  settings['chrg_rate'] = pset.chrg_rate
  settings['dchrg_rate'] = pset.dchrg_rate
  settings['DC_or_CD'] = pset.DC_CD
  settings['cycles'] = pset.cycles  
  settings['cycle_delay'] = pset.cycle_delay
  settings['max_charge_time'] = pset.max_charge_time  
  settings['minV'] = pset.minV
  settings['prgm_id'] = pset.id
  #Force all the changes to widget values from the picked program
  #Some changes causes a cascade of changes reconciled in update_selects()  
  #first set trigger notice for update-selects that prgm is changing values, not user.
  settings['set_prgm'] = 1
  select_battype.value = settings['bat_type']
  maxmah_slider.value = int(settings['nominal_mah'])
  select_cells.value = str(settings['cells'])
  select_minV.value = str(settings['minV'])
  select_chrg_type.value = settings['chrg_type']
  select_chrg_rate.value = settings['chrg_rate']
  select_dchrg_rate.value = settings['dchrg_rate']
  DC_radio_group.active = int(settings['DC_or_CD'])
  select_cycles.value = settings['cycles']
  text_input.value = settings['run_text']
  use_input.value = settings['battery_use']
  print('finished pgm_set settings')
  #reset trigger notice to update-selects that prgm is not changing values.
  settings['set_prgm'] = 0
  #need to always keep settings_packet up to date
  get_settings_packet()

#Dropdown widget for database stored programs
select_prgm = Select(title = "Select Prgm to Run", value = "None", options = db_ops.get_prgms())
def select_prgm_handler(attr, old, new):
  #print('select_pgm btn worked')
  if new:
    print('Selected prgm is: ', new)
    if new != 'None':
      #query database using battery_use
      prgm_settings = db_ops.session.query(Programs).filter_by(battery_use=new).first() 
      print('prgm id returned is: ', prgm_settings.id)
      #q = db_ops.session.query(Programs).filter(Programs.battery_use == new).first()
      #apply the chosen program settings
      prgm_set(prgm_settings)
#Shucks! Next doesn't fire if select value not changed; there is no on_click event.
#Get around? Future conisderation? 
select_prgm.on_change('value', select_prgm_handler)

#btn to save settings as program
btn_savenew = Button(label="Save New", button_type = 'success')
def btn_savenew_handler():
  #print('button save new worked')
  save_op = 1
  print('btn save battery_use to be saved is: ', settings['battery_use']) 
  if len(settings['battery_use']) != 0:
    subsettings =  {'bat_type':settings['bat_type'], 'battery_use':settings['battery_use'], 'chrg_type':settings['chrg_type'], 
                  'chrg_rate':settings['chrg_rate'], 'dchrg_rate':settings['dchrg_rate'], 'nominal_mah':settings['nominal_mah'], 
                  'DC_or_CD':settings['DC_or_CD'], 'cycles':settings['cycles'], 'cells':settings['cells'], 
                  'minV':settings['minV'], 'cycle_delay':settings['cycle_delay'], 'max_charge_time':settings['max_charge_time']}
    print('going db')
    did_save = db_ops.to_db(save_op, subsettings)
    print('out of save')
    if did_save:
      select_prgm.options = db_ops.get_prgms()  
      msg = 'New program settings saved as: [' + subsettings['battery_use']+']'
      print(msg)
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)   
    else:
      msg = 'Settings not saved; something went wrong.'
      print(msg)
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)      
btn_savenew.on_click(btn_savenew_handler)

btn_saveover = Button(label="Replace Program", button_type = 'primary')
def btn_saveover_handler():
  #print('button save over worked')
  if settings['bat_type'] != 'None':  
    save_op = 2
    subsettings =  {'bat_type':settings['bat_type'], 'battery_use':settings['battery_use'], 'chrg_type':settings['chrg_type'], 
                  'chrg_rate':settings['chrg_rate'], 'dchrg_rate':settings['dchrg_rate'], 'nominal_mah':settings['nominal_mah'], 
                  'DC_or_CD':settings['DC_or_CD'], 'cycles':settings['cycles'], 'cells':settings['cells'], 
                  'minV':settings['minV'], 'cycle_delay':settings['cycle_delay'], 'max_charge_time':settings['max_charge_time']} 
    print('savenew: max charge time: ', settings['max_charge_time'])
    did_save = db_ops.to_db(save_op, subsettings, settings['prgm_id'])
    if did_save:
      select_prgm.options = db_ops.get_prgms()  
      msg = 'Settings saved as: ' + subsettings['battery_use']
      print(msg)
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)   
    else:
      msg = 'Settings not saved; something went wrong.'
      print(msg)
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)       
btn_saveover.on_click(btn_saveover_handler)

btn_delete = Button(label="Delete Program", button_type = 'danger')
def btn_delete_handler():
  #print('button delete worked')
  delete_op = 3
  subsettings =  {'battery_use':settings['battery_use']} 
  print('prgm id in delete is: ', settings['prgm_id'])
  did_delete = db_ops.to_db(delete_op, subsettings, settings['prgm_id'])
  if did_delete:
    settings.update(reset_settings)
    select_battype.value = settings['bat_type']
    maxmah_slider.value = int(settings['nominal_mah'])
    select_cells.value = str(settings['cells'])
    select_minV.value = str(settings['minV'])
    select_chrg_type.value = settings['chrg_type']
    select_chrg_rate.value = settings['chrg_rate']
    select_dchrg_rate.value = settings['dchrg_rate']
    DC_radio_group.active = settings['DC_or_CD']
    select_cycles.value = settings['cycles']
    text_input.value = settings['run_text']
    use_input.value = settings['battery_use']
    select_prgm.value = 'None'
    select_prgm.options = db_ops.get_prgms()
    msg = 'Program: [' + subsettings['battery_use'] + '] deleted.'
    print(msg)
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
  else:
    msg = 'Program not deleted; not found.'
    print(msg)
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
btn_delete.on_click(btn_delete_handler)    

textsource = ColumnDataSource(data=dict(time = [],msg = []))
columns = [ 
  TableColumn(field="time", title="Time"), 
  TableColumn(field="msg", title="Msg", width = 600)]
data_table = DataTable(source=textsource, columns=columns, width=600) 

button_save = Button(label="Save Run Data", button_type = 'warning')
def button_save_handler():
  global read_data
  #print('button save worked')
  run_modes= {'bat_type':settings['bat_type'], 'chrg_type':settings['chrg_type'], 'nominal_mah':settings['nominal_mah'], 
              'DC_or_CD':settings['DC_or_CD'], 'cycles':settings['cycles'], 'cells':settings['cells'], 'run_text':settings['run_text']}
  excel_out = imax.write_excel_file(run_modes, settings['final_read'], read_data, settings['settings_dict'])
  msg = 'Data saved to: ' + excel_out
  print(msg)
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)     
button_save.on_click(button_save_handler)

def text_update(t, msg):
  global data_table
  print('msg: ', t, msg)
  new_data = dict(time=[t], msg=[msg],) 
  textsource.stream(new_data, 20) #adding the value is a scrolloff lines
  data_table.update()

import imax

def get_final_data():
  #triggers final values to be read from imax 
  global device_dict
  device = device_dict['device']
  EndPt_out = device_dict['EndPt_out']
  EndPt_in = device_dict['EndPt_in']
  final_out = [0x0f,	0x03, 0xfe,	0x000, 0xfe, 0xff, 0xff] + [0]*57
  w_out = device.write(EndPt_out, final_out)
  final_data = device.read(EndPt_in.bEndpointAddress,EndPt_in.wMaxPacketSize)
  if final_data:
    final_mah = str(final_data[5] * 256 + final_data[6])            #energy
    final_t = str(final_data[7] * 256 + final_data[8])              #timer    sec 
    final_V = str((final_data[9] * 256 + final_data[10]) / 1000.0)  #voltage, V
    final_T = str(final_data[14])                                   #Temperature, deg C, if F???

    settings['final_read'] = {'final_mah':final_mah, 'final_t':final_t, 'final_V':final_V, 'final_T':final_T}
  msg = 'Run completed. Final values: ' + final_mah + ' mah; '+ final_V + ' V; ' + final_t + ' s.'
  print(msg)
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
  #set to idle again
  imax_settings_out =[0x0f, 0x03, 0x5a, 0x00, 0x5a, 0xff, 0xff] + [0]*57 
  w_out = device.write(ep_out, imax_settings_out)
  idle_settings = device.read(ep_in.bEndpointAddress,ep_in.wMaxPacketSize) 
  #print('idle_settings are: ', idle_settings)   
  
def start_device():
  #----sets up device if connected, returns imax settings, configures, and sets data dictionary---
  #check for device, if not there wait for connection.
  global read_data
  global device_dict
  device_str = imax.find_my_device() #returns True if device found 
  if "No" in device_str:
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), device_str) 
    print(device_str)
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax offline. Cycling for one minute.')
    nowtime = datetime.datetime.now()
    futuretime = datetime.datetime.now() + datetime.timedelta(minutes = 1)
    while "No" in device_str:
      device_str = imax.find_my_device() #returns msg which has "No" in it ,if device not found
      if "No" in device_str:
        if datetime.datetime.now()> futuretime:
          text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Could not find device; check device and connection.')  
          return False
      time.sleep(1)  
  print('device found')
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), device_str)      
  #device found, engage device, get parameters and dictionaries
  get_settings_packet()
  if settings_packet:
    device_dict, read_data, settings_dict, data_out_packet = imax.start_imax(settings_packet)
  #check cells and battery voltage max limits  
  settings['settings_dict'] = settings_dict
  battery_V = settings_dict['bat_V'] #obtained from idling packet, but transferred as V not mV
  #print('limit test: ', limits[settings['bat_type']][1]*int(settings['cells']), battery_V*1000) 
  if limits[settings['bat_type']][1]*int(settings['cells']) < battery_V:
    print('Battery voltage is too high for number of cells specified.')
    msg = 'Battery voltage is too high for number of cells specified.'
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
    return False
  #print('read_data is: ', read_data)
  #Is imax running?
  #translation of next line: from read_data dict, get last element (as a list) and extract the value
  print('run_status is ', read_data['run_status'][-1:][0]) 
  #check if at least got some kind or read back from Imax. Is status > default (0)
  if len(read_data['run_status'][-1:]) > 0:
    settings['run_status'] = read_data['run_status'][-1:][0]  #stored as integer
    settings['data_out_packet'] = data_out_packet
    msg = 'Imax device found; settings transferred.' 
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
    return True
  else:
    msg = 'Problem transferring or starting Imax.'  
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
    return False
        
def add_lines(plot, source, cells_num = 0):
  #called from button_startstop_handler if bat_type LiPO, note that cells must be > 1
  color_list = ['orange', 'yellow', 'green', 'blue', 'violet', 'darkmagenta']
  if cells_num > 1:
    for i in range(cells_num):
      p1.line(x = 'timer', y = 'cell'+ str(i+1), source = source, color = color_list[i], line_width = 2)

#Button to set up and start Imax B6 Mini
button_startstop = Button(label = "Start", button_type = 'success')
def button_startstop_handler():
  global button_startstop
  global settings_packet
  #print('button start worked')
  #read btn label and isas driver for condition
  #label  = "Start": and device_started = False is initial start up condition
  if button_startstop.label == "Start":
    button_startstop.label = "Connecting"
    #Find and initialize Imax device, returns True if found and started.    
    settings['device_started'] = start_device()
    #returns True if device found,connected and started
    if settings['device_started']:
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax collecting data.') 
      #print('device found')      
      button_startstop.label = "Stop" 
      settings['start_cycle'] = curdoc().add_periodic_callback(update, 10000)
    else: #device was not started
      button_startstop.label = "Start" 
      msg = 'Imax start failed. See above messages for possible causes'     
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
      settings['run_status'] = 0      
  else: #deal with stop conditions; user pressed app stop button, or run_status > 1 (imax buttons pressed.)
    if button_startstop.label == "Stop":
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Run stopped because status is ' + str(settings['run_status']))
      curdoc().remove_periodic_callback(settings['start_cycle'])
      get_final_data()      
      button_startstop.label = "Start" 
  if "Li" in settings['bat_type']:
    add_lines(p1, source, cells_num = int(settings['cells']))
button_startstop.on_click(button_startstop_handler)

def read_imax():
  #Called by the Update) callback fcn to read current values from imax
  global read_data
  global device_dict
  # see above call to start_imax() for globals set from imax.py
  global out_data
  global old_time
  global base_time
  device = device_dict['device']
  EndPt_out = device_dict['EndPt_out']
  EndPt_in = device_dict['EndPt_in']

  #send the host->imax packet to trigger imax usb-uart to fill buffer
  w_out = device.write(EndPt_out, settings['data_out_packet']) 
  #Read the data out of the buffer ..imax->host  
  try:
    data = device.read(EndPt_in.bEndpointAddress,EndPt_in.wMaxPacketSize) #using more general form of Endpoint_IN attributes 
  except Exception as e:
    print('Something went wrong: no data incoming; error is: ', e) 
  
  #Parse the current hex data read from imax for output to the plots
  out_data['mah'] = [int(str(data[5]*256 + data[6]))]  #capacity, mah
  # if cycling, we need to acount for the Imax tiime shifting back to 0.
  if int(str(data[7]*256 + data[8])) < old_time: base_time = old_time 
  out_data['timer'] = [int(str(data[7]*256 + data[8]))+ base_time]   #seconds
  old_time = int(str(data[7]*256 + data[8])) + base_time
  out_data['volts'] = [int(str(data[9]*256 + data[10]))]          #volts
  out_data['current'] = [int(str(data[11]*256 + data[12]))]       #amps
  out_data['ext_T'] = [int(str(data[13]))]
  out_data['internal_T'] = [int(str(data[14]))]                   #deg. C?
  out_data['cell1'] = [int(str(data[17]*256 + data[18]))]         #cell 1 etc.
  out_data['cell2'] = [int(str(data[19]*256 + data[20]))]
  out_data['cell3'] = [int(str(data[21]*256 + data[22]))]
  out_data['cell4'] = [int(str(data[23]*256 + data[24]))]
  out_data['cell5'] = [int(str(data[25]*256 + data[26]))]
  out_data['cell6'] = [int(str(data[27]*256 + data[28]))]
  #print('from read_imax: out_data ', out_data)
  read_data['mah'].append(int(str(data[5]*256 + data[6])))       #capacity, mah
  read_data['timer'].append(int(str(data[7]*256 + data[8])))     #seconds
  read_data['volts'].append(int(str(data[9]*256 + data[10])))    #volts
  read_data['current'].append(int(str(data[11]*256 + data[12]))) #amps
  read_data['ext_T'].append(int(str(data[13])))
  read_data['internal_T'].append(int(str(data[14])))             #deg. C?
  read_data['cell1'].append(int(str(data[17]*256 + data[18])))
  read_data['cell2'].append(int(str(data[19]*256 + data[20])))
  read_data['cell3'].append(int(str(data[21]*256 + data[22])))
  read_data['cell4'].append(int(str(data[23]*256 + data[24])))
  read_data['cell5'].append(int(str(data[25]*256 + data[26])))
  read_data['cell6'].append(int(str(data[27]*256 + data[28])))
 
  #print the data to console(same sequence Milek7 used with hidapi..apreciated effort.
  #dump to console (for checking). Comment out or deleted for faster response
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
  
  #Pull out the run status so can see if run stopped: see docs for values?
  settings['run_status'] = int(str(data[4]))
  return settings['run_status'], out_data

#initialize read_data dictionary for plots
#to expand the resolution on plots would need to first get current battery 
#voltage by sending an idle request at this stage, but we have not initialized
#the imax yet. Could use source.patch?
out_data = {'mah':[0], 'timer':[0], 'volts':[0], 'current':[0], 
              'ext_T':[0], 'internal_T':[0], 'cell1':[0], 'cell2':[0],
              'cell3':[0],'cell4':[0], 'cell5':[0], 'cell6':[0]}
#time_interval = 5 #seconds

source = ColumnDataSource(data = out_data)

#Generate two plots, for capacity and voltage
p = figure(plot_width=400, plot_height=400)
p.title.text = "Capactiy vs. Time"
p.title.text_color = "black"
p.title.text_font = "arial"
p.title.text_font_style = "bold"
p.yaxis.minor_tick_line_color = "black"
p.xaxis.axis_label = "Time, s"
p.yaxis.axis_label = "Capacity (mah)"
r_cap = p.line(x = 'timer', y = 'mah', source = source, color="red", line_width=2)

#Set the voltabe plot; complicated a  bit by battery type
p1 = figure(plot_width=400, plot_height=400)
p1.title.text = "Voltage vs. Time"
p1.title.text_color = "black"
p1.title.text_font = "arial"
p1.title.text_font_style = "bold"
p1.yaxis.minor_tick_line_color = "black"
p1.xaxis.axis_label = "Time, s"
p1.yaxis.axis_label = "Voltage. mV"
rx = p1.line(x = 'timer', y = 'volts', source = source, color = "firebrick", line_width=2)

def update():
  #Bokeh method periodic callback referenced by btnstartstop
  global out_data
  global source
  global read_data
  device = device_dict['device']
  if device:
    #note "new_data" is bokeh specific to only add to source
    settings['run_status'], new_data = read_imax()
    #At least first 2 packets have run_status = 3, so bypass before checking
    #print('status: ', run_status, 'length of read_data: ',len(read_data['mah']))
    if len(read_data['mah']) > 2: 
      if settings['run_status'] < 2 and button_startstop.label == "Stop":
        source.stream(new_data)
      else:
        if settings['run_status'] == 2:
          msg = '; User stopped run from imax stop button.'
        if settings['run_status'] == 3:
          msg = '; Imax stopped run.'
        text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
        button_startstop_handler()
  else:
    msg = '; Device no longer connected.'
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
    button_startstop_handler()    

#w1 = row(select_battype, select_chrg_type) #, width = 300) #sizing_mode = 'fixed')
w1 = column(select_battype, select_chrg_type, select_cells) #, width = 300) #sizing_mode = 'fixed')
w2 = column(maxmah_slider) #, sizing_mode='fixed')
w3 = column(select_chrg_rate, select_dchrg_rate, select_minV)
w4 = column(text_input) #, sizing_mode = 'fixed')
w5 = column(button_startstop, button_save )#, sizing_mode ='fixed')
w6 = column(DC_radio_group, select_cycles)
w7 = column( use_input,select_prgm)
w8 = column(btn_savenew, btn_saveover, btn_delete)
w9 = column(data_table)

curdoc().add_root(notice1)
Layit = gridplot([[column(w1.children+w2.children+w3.children+w4.children+w5.children+w6.children+w7.children+w8.children+w9.children), column([p, p1])]]) 

curdoc().add_root(Layit) 
#curdoc().add_root(data_table)
#lays out in one long row at top
#Layit = gridplot([w1.children+w2.children+w3.children+w4.children+w5.children+w5.children], ncol = 1) 
#Layit = gridplot([w1.children, w2.children, w3.children, w4.children, w5.children], ncol = 1) 
#curdoc().add_root(Layit) 
