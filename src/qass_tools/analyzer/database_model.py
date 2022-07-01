from xmlrpc.client import Boolean
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DATETIME, BOOLEAN, Identity
from sqlalchemy.orm import declarative_base, relationships
from datetime import datetime

Base = declarative_base()


class ProcessBuffer(Base):
	__tablename__ = "process_buffer"
	id = Column(Integer, Identity(start = 1), primary_key = True)
	process_id = Column(Integer, nullable = False) # TODO FK
	projectid = Column(BigInteger, nullable = False) # TODO FK
	buffer_id = Column(BigInteger, nullable = False, default = 0)
	date_creation = Column(DATETIME, nullable = False, default = datetime.now())
	date_modified = Column(DATETIME, nullable = False, default = datetime.now())
	partition_uuid = Column(String, nullable = False, default = "{000-000-000}") # TODO this is wrong
	extid = Column(BigInteger, nullable = False, default = 0)
	path = Column(String, nullable = True)
	filename = Column(String, nullable = False) #TODO this might be wrong here since it's not in the original
	comment = Column(String, nullable = True)
	duration = Column(BigInteger, nullable = False)
	sizebytes = Column(BigInteger, nullable = False)
	datamode = Column(Integer, nullable = False)
	datatype = Column(Integer, nullable = False)
	dataflags = Column(Integer, nullable = False)
	channel = Column(Integer, nullable = False)
	compress = Column(Integer, nullable = False)
	fcompress = Column(Integer, nullable = False, default = 1)
	auxpara0 = Column(Integer, nullable = False, default = 0)
	auxpara1 = Column(Integer, nullable = False, default = 0)
	auxpara2 = Column(Integer, nullable = False, default = 0)
	auxpara3 = Column(Integer, nullable = False, default = 0)
	auxpara4 = Column(Integer, nullable = False, default = 0)
	auxpara5 = Column(BigInteger, nullable = False, default = 0)
	simmode = Column(Integer, nullable = False, default = -1)
	skip_samples = Column(BigInteger, nullable = False)
	skip_time = Column(BigInteger, nullable = False)
	trunc_samples = Column(BigInteger, nullable = False)
	trunc_time = Column(BigInteger, nullable = False)
	skip_lofrq = Column(Integer, nullable = False)
	trunc_hifrq = Column(Integer, nullable = False)
	buffer_idx = Column(Integer, nullable = False, default = 0)
	process = Column(Integer, nullable = False, default = -1)
	processrange = Column(Integer, nullable = False, default = 1)
	subprocess  = Column(Integer, nullable = False)
	polycyclic_part = Column(Integer, nullable = False)
	polycyclic_id = Column(Integer, nullable = False, default = -1)
	polycyclic_num = Column(Integer, nullable = False)
	modusagemask = Column(BigInteger, nullable = False, default = 0)
	datafilever = Column(Integer, nullable = False, default = 0)
	bytespersample = Column(Integer, nullable = False, default = 0)
	samplesperframe = Column(Integer, nullable = False, default = 0)
	adctype = Column(Integer, nullable = False, default = 0)
	adcbitres = Column(Integer, nullable = False, default = 0)
	samplefreq = Column(Integer, nullable = False, default = 0)
	interpolated = Column(BOOLEAN, nullable = False, default = 0)
	bufcomppara_txt = Column(String, nullable = True)
	transformations_txt = Column(String, nullable = True)
	islikelymeasure = Column(BOOLEAN, nullable = False, default = 1)
	measurerestarted = Column(BOOLEAN, nullable = False, default = 0)
	flags = Column(Integer, nullable = False, default = 0)

