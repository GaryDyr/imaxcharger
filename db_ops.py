#Database utility module used by run_imax.py to handle database 
#functions for storing,updating, and removing settings program entries.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from sqlalchemy import inspect
from sqlalchemy import Table
from sqlalchemy.sql import text
#from sqlalchemy.ext.automap import automap_base
from tabledef import *

engine = create_engine('sqlite:///imax_programs.db', echo = True)
inspector = inspect(engine)
# Get table information
print('inspector returned tables: ' ,inspector.get_table_names())

for table_name in inspector.get_table_names():
  for column in inspector.get_columns(table_name):
    print("Column: %s" % column['name'])

Session = sessionmaker(bind = engine)
session = Session()

prgm_list = []
id_list = []
prgm_id = 1

def get_prgms():
  global prgm_list
  global id_list
  global prgm_index
  b_types = ['NiMH', 'NiCd', 'LiPO', 'LiFe', 'LiION', 'LiHV', 'Pb']
  #bq = Table('programs', metadata, autoload=True, autoload_with=engine)
  #for instance in session.query(Programs).order_by(Programs.battery_type):
  #  print(instance.battery_type)
  #get all row (program) object entries
  print('in db_ops.et_prmgs')
  print('prgm count is = ', session.query(Programs).count())
  if session.query(Programs).count() > 0:
    q = session.query(Programs).all()
    olist = []
    for r in q:
      rseq = (r.battery_type, r.battery_use, r.id)
      olist.append(rseq) #add tuple to list
    #nl = [r.battery_use for r.battery_type in b_types]
    #sort list by the bat_types sorting list
    #for each item in olist get it according to     
    slist = sorted(olist, key = lambda item: b_types.index(item[0]))
    print('slist is: ', slist)
    prgm_list = [x[1] for x in slist] # get the battery_use text blurbs from sorted list
    prgm_list = ['None'] + prgm_list
    print('prgm_list is: ', prgm_list)   
    #prgm_index = [x[2] for x in slist]  
    return prgm_list
  else:
    return ['No Prgms']
#def update_settings(id_list, olist, prgm_id):
   
def to_db(op, p, id = None):
  #p is current dictionary of settings, supplied by call from run_imax.btn_savenew.
  print('to_db id is: ', id)  
  if op == 1:
  # Insert a new set of settings into table
    new_prgm = Programs(battery_type = p['bat_type'], battery_use = p['battery_use'], 
                       chrg_type = p['chrg_type'], chrg_rate = p['chrg_rate'], dchrg_rate = p['dchrg_rate'],
                       nominal_mah = p['nominal_mah'], DC_CD = p['DC_or_CD'], 
                       cycles = p['cycles'], battery_cells = p['cells'], minV = p['minV'], 
                       cycle_delay = p['cycle_delay'], max_charge_time = p['max_charge_time'])
    session.add(new_prgm)
    session.commit()
    return True

  #deal with replacing values
  if op == 2 and id:
    print('in op 2 with id: ', id)
    pset = {'battery_type': p['bat_type'], 
            'battery_use': p['battery_use'], 
            'nominal_mah': p['nominal_mah'],
            'battery_cells': p['cells'],
            'chrg_type':p['chrg_type'],
            'chrg_rate':p['chrg_rate'],
            'dchrg_rate':p['dchrg_rate'],
            'DC_CD':p['DC_or_CD'],
            'cycles':p['cycles'],
            'cycle_delay':p['cycle_delay'],
            'max_charge_time':p['max_charge_time'],
            'minV':p['minV']}
    str_id = text(str(id))      
    pm = session.query(Programs).filter_by(id = str_id)
    pm.update(pset, synchronize_session = False)
    session.commit()
    #session.flush()
    return True
  #deal with deleting a row    
  if op == 3 and id:
    print('Deleting prgm: ', p['battery_use'])
    session.query(Programs).filter_by(id=id).delete()
    session.commit()
    return True
  return False #something went wrong 
    
"""
#USED FOR TESTING, OR IF DESIRED CAN BE USED TO PRESET PROGRAMS USING  python db_ops.py. 
#REQUIRES tabledef.py MODULE, IN SAME FOLDER, AND THAT tabledef.py HAS BEEN PREVIOUSLY RUN 
#E.G., (python tabledef.py)

#TO GENERATE THE SQLITE DATABASE TABLE programs OF CLASS Programs.
p = {'bat_type':'NiMH', 'battery_use':'NiMH, Tiger 60 TX, Charge', 'chrg_type':'Charge', 'chrg_rate':'100', 'dchrg_rate':'100', 
                       'nominal_mah':'2300', 'DC_or_CD':'Discharge/Charge', 'cycles':'1', 'cells':'8', 'minV':'1100', 
                       'cycle_delay':'10', 'max_charge_time':'180'}
                       
                       

p2 = {'bat_type':'LiPO', 'battery_use':'Sukhoi Electric, liPo 3x', 'chrg_type':'Charge', 'chrg_rate':'100', 'dchrg_rate':'300', 
                       'nominal_mah':'1450', 'DC_or_CD':'Discharge/Charge', 'cycles':'1', 'cells':'3', 'minV':'3100', 
                       'cycle_delay':'10', 'max_charge_time':'180'}                      

                       
p3 = {'bat_type':'NiCd', 'battery_use':'NiCd, Tiger 60 RX', 'chrg_type':'Charge', 'chrg_rate':'100', 'dchrg_rate':'100', 
                       'nominal_mah':'2300', 'DC_or_CD':'Discharge/Charge', 'cycles':'1', 'cells':'4', 'minV':'1100', 
                       'cycle_delay':'10', 'max_charge_time':'180'} 

p4 = {'bat_type':'NiMH', 'battery_use':'NiMH, Smith Mini Flash TX, Charge', 'chrg_type':'Charge', 'chrg_rate':'100', 'dchrg_rate':'100', 
                       'nominal_mah':'2300', 'DC_or_CD':'Discharge/Charge', 'cycles':'1', 'cells':'8', 'minV':'1100', 
                       'cycle_delay':'10', 'max_charge_time':'180'}                       
           
  
def add_prgm(pm):
#caLLED run_imax 
  ptest = Programs(
    battery_type = pm['bat_type'], 
    battery_use = pm['battery_use'], 
    nominal_mah = pm['nominal_mah'],
    battery_cells = pm['cells'],
    chrg_type = pm['chrg_type'],
    chrg_rate = pm['chrg_rate'],
    dchrg_rate = pm['dchrg_rate'],
    DC_CD = pm['DC_CD'],
    cycles = pm['cycles'],
    cycle_delay = pm['cycle_delay'],
    max_charge_time = pm['max_charge_time'],
    minV = pm['minV'],
    )
  session.add(ptest)
  session.commit()  

#for testing pruposes
add_prgm(p)
add_prgm(p2)
add_prgm(p3)
add_prgm(p4)
for instance in session.query(Programs).order_by(Programs.id):
  print(instance.battery_type)
y = get_prgms()
print(y)
"""