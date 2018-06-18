"""
Create a config file
 #bat_type - battery type say message how many times
 #allowable types: NiMH', 'NiCd', 'LiPO', 'LiFe', 'LiION', 'LiHV' 
"""
import os
import sys
import configparser
config = configparser.ConfigParser(allow_no_value = True)
config['DEFAULT'] = {'bat_type': 'NiMH', 
                                 'cells':'1', 
                                 'slider_max':str(4050)}
config['BatterySettings'] = {}
# Allowable types: NiMH, NiCd, LiPO, LiFe, LiION, LiHV"
config.set("BatterySettings", "# Set battery type here:")
config.set("BatterySettings", "# Allowable types: NiMH, NiCd, LiPO, LiFe, LiION, LiHV")
config['BatterySettings']['bat_type'] = 'NiMH'
config['BatterySettings']['cells'] = '1'

config['SelectorSettings'] = {}
config.set('SelectorSettings', '# Set limits for selection widgets here.')
config['SelectorSettings']['slider_max'] = '4050'
config['SelectorSettings']['nominal_mah_strt'] = '500'


fn = 'imaxconfig.ini'
settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), fn)
with open(settings_file, 'w') as configfile:
  config.write(configfile)
