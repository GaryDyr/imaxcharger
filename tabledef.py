# Creates settings programs table using SQLalechemy ORM.
#Execute with:
#python tabledef.py 
import os
import sys
from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///imax_programs.db', echo=True)
Base = declarative_base()
 
########################################################################
#see https://pythonspot.com/orm-with-sqlalchemy/
########################################################################

class Programs(Base):
  """"""
  __tablename__ = "programs"

  id = Column(Integer, primary_key=True)
  battery_type = Column(String)
  battery_use = Column(String)
  nominal_mah = Column(String)
  battery_cells = Column(String)
  chrg_type = Column(String)
  chrg_rate = Column(String)
  dchrg_rate = Column(String)
  DC_CD = Column(String)
  cycles = Column(String)
  cycle_delay = Column(String)
  max_charge_time = Column(String)
  minV = Column(String)

# create tables
Base.metadata.create_all(engine)
#Execute with:
#python tabledef.py 
