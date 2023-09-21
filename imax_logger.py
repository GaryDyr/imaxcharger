"""
Bokah interface for Imax B6 mini charnger
Requires: bokeh - pip install bokuh
but calls imax_0.py; see imax_0.py for additional necessary library packages
"""

import sys
import time
import datetime
from bokeh.models import ColumnDataSource, Slider, DataTable, TableColumn
from bokeh.plotting import figure, output_file, show
from bokeh.io import output_file, show
from bokeh.layouts import column, row
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider, RadioGroup, Div, TextInput
from bokeh.layouts import gridplot, layout
from bokeh.plotting import curdoc 
from bokeh.driving import linear
from bokeh.models.callbacks import CustomJS

#specify varibles for the  inputs.
bat_type = ""
chrg_type = ""
nominal_mah = 0
DC_or_CD = "Discharge/Charge"
cycles = 1
cells = 4
run_text = "Enter run information"
time_interval = 10 #seconds
final_read = {'final_mah':"", 'final_t':"", 'final_V':"", 'final_T':""}
#next is set in start_device(), which is obtained from imax_0.start_imax
device_dict = {'device':None, 'EndPt_out':None, 'EndPt_in':None}
text_update = None 
settings_dict = {}
read_data = {}
data_out_packet = []
device_started = False
out_data = {}
start_cycle = None
run_status = 0
#create a dictionary of initial values to minimize global calls
settings = {
              'bat_type':bat_type, 
              'cells':cells, 
              'chrg_type':chrg_type, 
              'nominal_mah':nominal_mah, 
              'DC_or_CD':DC_or_CD, 
              'cycles':cycles,
              'device_started':device_started,
              'time_interval':time_interval,
              'start_cycle':start_cycle,
              'run_text':run_text,
              'run_status':run_status,
              'final_out':final_read,
              'data_out_packet':data_out_packet,
              'settings_dict':settings_dict,
              'device_dict':device_dict
           }

#Create the header for page
notice1 = Div(text="""The data input here are for logging identification and saving conditions, which are already manually chosen 
                on the imax. They do not set or reset the imax.""",
                sizing_mode = "scale_width")

select_battype = Select(title = "Battery Type", value ="", options = ['NiMH', 'NiCd', 'LiPO', 'LiFe', 'LiIO', 'LiHV'])
def select_battype_handler(attr, old, new):
  settings['bat_type'] = new
select_battype.on_change('value', select_battype_handler)

select_chrg_type = Select(title="Charge Type", value="Charge", options=["Charge", "Discharge", "Cycle", "Re-Peak", "AutoCharge", "Balance Charge", "Fast Charge", "Storage"])
def select_chrg_type_handler(attr, old, new):
  settings['chrg_type'] = new

select_chrg_type.on_change('value', select_chrg_type_handler)

maxmah_slider = Slider(start=50, end=24000, value=1, step=50, title="Bat. Specified Capacity, mah")
def maxmah_handler(attr, old, new):
  settings['nominal_mah'] = new
maxmah_slider.on_change('value', maxmah_handler)

DC_radio_group = RadioGroup(labels=["Discharge/Charge", "Charge/Discharge"], active=0)
def DC_radio_handler(new):
  settings['DC'] = new  
DC_radio_group.on_click(DC_radio_handler)

select_cells = Select(title = "No. of Cells", value ="4", options = [str(i) for i in range(1,13)])
def select_cells_handler(attr, old, new):
  settings['cells'] = new
select_cells.on_change('value', select_cells_handler)

#imax discharge/charge # of cycles; imax limit is 5
#no way to read this from imax only shows up in set up packet
select_cycles = Select(title = "Cycles", value ="1", options = [str(i) for i in range(1,6)])
def select_cycles_handler(attr, old, new):
  settings['cycles'] = new
select_cycles.on_change('value', select_cycles_handler)

text_input = TextInput(value="Enter run information", title="Run Info::")
def text_input_handler(attr, old, new):
  settings['run_text'] = new
text_input.on_change("value", text_input_handler)

textsource = ColumnDataSource(data=dict(time = [],msg = []))
columns = [ 
  TableColumn(field="time", title="Time"), 
  TableColumn(field="msg", title="Msg", width = 600)]
data_table = DataTable(source=textsource, columns=columns, width=600) 

button_save = Button(label="Save Run", button_type = 'warning')
def button_save_handler():
  global read_data
  print('button save worked')
  run_modes= {'bat_type':settings['bat_type'], 'chrg_type':settings['chrg_type'], 'nominal_mah':settings['nominal_mah'], 
              'DC_or_CD':settings['DC_or_CD'], 'cycles':settings['cycles'], 'cells':settings['cells'], 'run_text':settings['run_text']}
  excel_out = imax_0.write_excel_file(run_modes, settings['final_read'], read_data, settings['settings_dict'])
  msg = 'Data saved to: ' + excel_out
  print(msg)
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)     
button_save.on_click(button_save_handler)

def text_update(t, msg):
  global data_table
  print('time and msg: ', t, msg)
  new_data = dict(time=[t], msg=[msg],) 
  textsource.stream(new_data, 20) #adding the value is a scrolloff lines
  data_table.update()

import imax_0

def check_device_status():
  global device_dict
#used by startstop btn handler to determine if imax start btn was pressed, or imax running.
  #global device_dict
  EndPt_out = device_dict['EndPt_out']
  EndPt_in = device_dict['EndPt_in']
  device = device_dict['device']
  #send host->imax packet to trigger imax to do imax->host transfer
  #make sure device is still connected
  if device:
    w_out = device.write(EndPt_out, settings['data_out_packet'])    
    data = device.read(EndPt_in.bEndpointAddress,EndPt_in.wMaxPacketSize)  
    settings['run_status'] = int(str(data[4]))
    return settings['run_status']
  else:
   print('Check device failed.')
   return None
  
def get_final_data():
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
    final_T = str(final_data[14])                              #Temperature, deg C, if F???
    #int temp 
    settings['final_read'] = {'final_mah':final_mah, 'final_t':final_t, 'final_V':final_V, 'final_T':final_T}
  msg = 'Run completed. Final values: ' + final_mah + ' mah; '+ final_V + ' mV; ' + final_t + ' s.'
  print(msg)
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)   
  
def start_device():
  global read_data
  global device_dict
  #sets up device if connected, returns imax settings, configrs, and sets data dictionary.
  #check for device, if not there wait for connection.
  device_str = imax_0.find_my_device() #returns True if device found 
  if "No" in device_str:
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), device_str) 
    print(device_str)
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax offline. Cycling for one minute.')
    nowtime = datetime.datetime.now()
    futuretime = datetime.datetime.now() + datetime.timedelta(minutes = 1)
    while "No" in device_str:
      device_str = imax_0.find_my_device() #returns msg which has "No" in it ,if device not found
      if "No" in device_str:
        if datetime.datetime.now()> futuretime:
          text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Could not find device; check device and connection.')  
          return False
      time.sleep(1)  
  print('device found')

  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), device_str)      
  #device was found, engage device, get parameters and dictionaries
  device_dict, read_data, settings_dict, data_out_packet = imax_0.start_imax()
  print('Loading settings)  
  settings['settings_dict'] = settings_dict
  settings['data_out_packet'] = data_out_packet
  
  #Determine if device is idling, or already running: run_status = 2 or 3, or is running = 1
  settings['run_status'] = check_device_status()
  nowtime = datetime.datetime.now()
  futuretime = datetime.datetime.now() + datetime.timedelta(minutes = 1)
  text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Waiting for Imax button press for one minute.')  
  while settings['run_status'] > 1:
    settings['run_status'] = check_device_status()
    if datetime.datetime.now()> futuretime:
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax button not pressed in 1 min...aborting start.')  
      return False      
    time.sleep(1)  
  print('out of loop run_status is: ', settings['run_status'])          
  return True

def add_lines(plot, source, cells_num = 0):
  #called from button_startstop_handler if bat_type LiPO, note cells must be > 1
  color_list = ['orange', 'yellow', 'green', 'blue', 'violet', 'darkmagenta']
  if cells_num > 1:
    for i in range(cells_num):
      p1.line(x = 'timer', y = 'cell'+ str(i+1), source = source, color = color_list[i], line_width = 2)

button_startstop = Button(label = "Start", button_type = 'success')
def button_startstop_handler():
  global button_startstop
  #read btn label and isas driver for condition
  #label  = "Start": and device_started = False is initial start up condition
  if button_startstop.label == "Start":
    button_startstop.label = "Connecting" 
    settings['device_started'] = start_device()
    #returns True if device found,connected and started
    if settings['device_started']:
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax found & running.') 
      button_startstop.label = "Stop"      
      settings['start_cycle'] = curdoc().add_periodic_callback(update, 10000)
      print('device found')
    else:
      if not settings['device_started']:
        button_startstop.label = "Start"  
        text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Imax start failed. Check everything') 
  else: #deal with stop conditions; user pressed app stop button, or run_status > 1 (imax buttons pressed.)
    if button_startstop.label == "Stop":
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Run stopped.')
      curdoc().remove_periodic_callback(settings['start_cycle'])
      get_final_data()      
      button_startstop.label = "Start" 
  if "Li" in settings['bat_type']:
    add_lines(p1, source, cells_num = int(settings['cells']))
    
  
button_startstop.on_click(button_startstop_handler)

def read_imax():
  global read_data
  global device_dict
  # see above call to start_imax() for globals set from imax.py
  #global data_out_packet
  global out_data
  #global run_status

  device = device_dict['device']
  EndPt_out = device_dict['EndPt_out']
  EndPt_in = device_dict['EndPt_in']

  #send the host->imax packet to trigger imax to fill buffer and do imax->host transfer
  #make sure device is still connected
  w_out = device.write(EndPt_out, settings['data_out_packet'])    
  try:
    data = device.read(EndPt_in.bEndpointAddress,EndPt_in.wMaxPacketSize) #using more general form of Endpoint_IN attributes 
  except Exception as e:
    print('Something went wrong: no data incoming; error is: ', e) 
    sys.exit() 
  
  #Parse the hex data
  out_data['mah'] = [int(str(data[5]*256 + data[6]))]             #capacity, mah
  out_data['timer'] = [int(str(data[7]*256 + data[8]))]           #seconds
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
 
  #print the data (same sequence Milek7 used with hidapi; much appreciated effort.
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
  
  #Has the charger been stopped by pressing the charger Stop button?
  settings['run_status'] = int(str(data[4]))
  return settings['run_status'], out_data

#initialize read_data dictionary for plots
out_data = {'mah':[0], 'timer':[0], 'volts':[0], 'current':[0], 
              'ext_T':[0], 'internal_T':[0], 'cell1':[0], 'cell2':[0],
              'cell3':[0],'cell4':[0], 'cell5':[0], 'cell6':[0]}
#time_interval = 5 #seconds
source = ColumnDataSource(data = out_data)

#Generate two plots, for capacity and voltage
p = column(plot_width=400, plot_height=400)
p.title.text = "Capactiy Input vs. Charge Time"
p.title.text_color = "black"
p.title.text_font = "arial"
p.title.text_font_style = "bold"
p.yaxis.minor_tick_line_color = "black"
p.xaxis.axis_label = "Time, s"
p.yaxis.axis_label = "Capacity Added(mah)"
r_cap = p.line(x = 'timer', y = 'mah', source = source, color="red", line_width=2)

#Set the voltabe plot; complicated a  bit by battery type
p1 = column(plot_width=400, plot_height=400)
p1.title.text = "Voltage vs. Charge Time"
p1.title.text_color = "black"
p1.title.text_font = "arial"
p1.title.text_font_style = "bold"
p1.yaxis.minor_tick_line_color = "black"
p1.xaxis.axis_label = "Time, s"
p1.yaxis.axis_label = "Voltage. mV"
rx = p1.line(x = 'timer', y = 'volts', source = source, color = "firebrick", line_width=2)
"""
#test block for adding lines
if "Li" in bat_type: 
  r1 = p1.line(x ='timer', y = 'cell1', source = source, color="orange", line_width=2)
  r2 = p1.line(x ='timer', y = 'cell2', source = source, color="yellow", line_width=2)
  r3 = p1.line(x ='timer', y = 'cell3', source = source, color="green", line_width=2)
  r4 = p1.line(x ='timer', y = 'cell4', source = source, color="blue", line_width=2)
  r5 = p1.line(x ='timer', y = 'cell5', source = source, color="violet", line_width=2)
  r6 = p1.line(x ='timer', y = 'cell6', source = source, color="darkmagenta", line_width=2)
"""
def update():
  global out_data
  global source
  global device_dict
  device = device_dict['device']
  if device:
    #note "new_data" is bokeh specific to only add to source
    settings['run_status'], new_data = read_imax()
    #print('read_imax returned run status: ', settings['run_status'])
    if settings['run_status'] < 2 and button_startstop.label == "Stop":
      source.stream(new_data) # 20)
    else:
      msg = '; User stopped run from imax stop button.'
      text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
      button_startstop_handler()
  else:
    msg = '; Device no longer connected.'
    text_update(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg)
    button_startstop_handler()    

"""
class Cycler(update()):
  msg = "Message from Cycler"
  start_cycle = staticmethod(curdoc().add_periodic_callback(update, 10000))
  stop_cycle = staticmethod(curdoc().remove_periodic_callback(start_cycle)) 
# create the widgets
"""    
    
    
#start_cycle = curdoc().add_periodic_callback(update, 10000) #time in milliseconds

#w1 = row(select_battype, select_chrg_type) #, width = 300) #sizing_mode = 'fixed')
w1 = column(select_battype, select_chrg_type, select_cells) #, width = 300) #sizing_mode = 'fixed')
w2 = column(maxmah_slider) #, sizing_mode='fixed')
w3 = column(text_input) #, sizing_mode = 'fixed')
w4 = column(button_startstop, button_save )#, sizing_mode ='fixed')
w5 = column(DC_radio_group, select_cycles)
w6 = column(data_table)
"""
Layit = layout([row(column(
[notice1],
  [w1],
  [w2],
  [w3],
  [w4],
  [w5],
  [data_table]), 
  column(p, p1))], sizing_mode='fixed')
"""
#Layit = gridplot([[column([p, p1]), column(w1.children+w2.children+w3.children+w4.children+w5.children)]])
curdoc().add_root(notice1)
Layit = gridplot([[column(w1.children+w2.children+w3.children+w4.children+w5.children,), column([p, p1])]]) 

curdoc().add_root(Layit) 
curdoc().add_root(data_table)
#curdoc().add_root(p)
#curdoc().add_root(p1)


  #interval is not constant,
  #based on derivative of capacity

# Add a periodic callback to be run every 500 milliseconds
#curdoc().add_periodic_callback(update, 500)

#for running textarea update following is one way to do it with js
"""
textare udating w/ jquery and textarea

var txt = document.getElementById('log');

setInterval(function(){txt.value += '\ntest';},2000);

<textarea id='log' rows=50 cols=60 autofocus></textarea>
"""
