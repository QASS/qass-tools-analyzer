import os
from datetime import datetime
from sqlalchemy import Float, create_engine, Column, Integer, String, BigInteger, DATETIME, BOOLEAN, Identity
from sqlalchemy.orm import Session, declarative_base

from qass_tools.analytic import buffer_parser as bp
# from analyzer.database_model import Base, ProcessBuffer






class BufferMetadataCache:

	def __init__(self, session, *sync_connections, Buffer_cls = None): # 		
		self._db = session
		self.Buffer_cls = Buffer_cls


	def synchronize_directory(self, *paths, sync_subdirectories = True):
		for path in paths:
			files = (file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file.endswith("000"))
			subdirectories = [os.path.join(path, directory) for directory in os.listdir(path) if not os.path.isfile(os.path.join(path, directory))]
			unsynchronized_files = self.get_non_synchronized_files(path, files)
			self.add_files(unsynchronized_files)
		if sync_subdirectories:
			self.synchronize_directory(*subdirectories, sync_subdirectories = True)


	def get_non_synchronized_files(self, filepath, files):
		"""calculate the difference between the set of files and the set of synchronized files

		:param filepath: full path to the files
		:type filepath: str
		:param files: filenames
		:type files: str
		:return: The set of files that are not synchronized
		"""
		synchronized_buffers = set(buffer.filename for buffer in self._db.query(self.BufferMetadata).all())
		unsynchronized_files = set(files).difference(synchronized_buffers)
		return unsynchronized_files

	def add_files(self, filepath, files):
		for file in files:
			pass
		

	@staticmethod
	def create_session(engine = None, db_url = "sqlite:///buffer_metadata_db"):
		if engine is None:
			engine = create_engine(db_url)
		session = Session(engine)
		BufferMetadataCache.__Base.metadata.create_all(engine, 
							tables = [BufferMetadataCache.__Base.metadata.tables["buffer_metadata"]])
		return session

	@staticmethod
	def buffer_to_buffer_metadata(buffer):
		"""Converts a Buffer object to a BufferMetadata database object by copying all the @properties from the Buffer
		object putting them in the BufferMetadata object

		:param buffer: Buffer object
		:type buffer: buffer_parser.Buffer
		"""
		properties = ("header_size", "process", "channel", "datamode", "datakind", "datatype", "process_time",
					"process_date_time", "db_header_size", "bytes_per_sample", "db_count", "full_blocks", "db_size",
					"db_sample_count", "frq_bands", "db_spec_count", "compression_frq", "compression_time", "avg_time",
					"avg_frq", "spec_duration", "frq_per_band", "sample_count", "spec_count", "adc_type", "bit_resolution",
					"fft_log_shift")
		if "/" in buffer.filepath:
			filename = buffer.filepath.split("/")[-1]
		elif "\\" in buffer.filepath:
			filename = buffer.filepath.split("\\")[-1]
		filepath = buffer.filepath[:-len(filename)]
		buffer_metadata = BufferMetadataCache.BufferMetadata(filename = filename, filepath = filepath)
		for prop in properties:
			try: # try to map all the buffer properties and skip on error
				setattr(buffer_metadata, prop, getattr(buffer, prop)) # get the @property method and execute it
			except:
				continue
		return buffer_metadata

		# return ProcessBuffer( # TODO create custom buffer thingy
		# process_id = buffer.,
		# projectid = buffer.,
		# buffer_id = buffer.,
		# date_creation = buffer.process_measure_timestamp,
		# date_modified = buffer.last_modification_date_time,
		# partition_uuid = buffer.,
		# extid = buffer.,
		# path = buffer.filepath,
		# comment = buffer.,
		# duration = buffer.spec_duration * buffer.spec_count,
		# sizebytes = buffer.file_size(),
		# datamode = buffer.datamode,
		# datatype = buffer.datakind,
		# dataflags = -1,
		# channel = buffer.channel,
		# compress = buffer.compression_time,
		# fcompress = buffer.compression_frq,
		# auxpara0 = buffer.,
		# auxpara1 = buffer.,
		# auxpara2 = buffer.,
		# auxpara3 = buffer.,
		# auxpara4 = buffer.,
		# auxpara5 = buffer.,
		# simmode = buffer.,
		# skip_samples = buffer.,
		# skip_time = buffer.,
		# trunc_samples = buffer.,
		# trunc_time = buffer.,
		# skip_lofrq = buffer.,
		# trunc_hifrq = buffer.,
		# buffer_idx = buffer.,
		# process = buffer.process,
		# processrange = buffer.,
		# subprocess = buffer.,
		# polycyclic_part = buffer.,
		# polycyclic_id = buffer.,
		# polycyclic_num = buffer.,
		# modusagemask = buffer.,
		# datafilever = buffer.,
		# bytespersample = buffer.bytes_per_sample,
		# samplesperframe = buffer.,
		# adctype = buffer.adc_type,
		# adcbitres = buffer.bit_resolution,
		# samplefreq = buffer.,
		# interpolated = buffer.,
		# bufcomppara_txt = buffer.,
		# transformations_txt = buffer.,
		# islikelymeasure = buffer.,
		# measurerestarted = buffer.,
		# flags = buffer.)


	__Base = declarative_base()
	class BufferMetadata(__Base):
		__tablename__ = "buffer_metadata"

		id = Column(Integer, Identity(start = 1), primary_key = True)
		projectid = Column(Integer)
		filepath = Column(String, nullable = False)
		filename = Column(String, nullable = False)
		header_size = Column(Integer)
		process = Column(Integer)
		channel = Column(Integer)
		datamode = Column(Integer) # TODO this is an ENUM in buffer_parser
		datakind = Column(Integer) # TODO this is an ENUM in buffer_parser
		datatype = Column(Integer) # TODO this is an ENUM in buffer_parser
		process_time = Column(BigInteger) # TODO this is an ENUM in buffer_parser
		process_date_time = Column(DATETIME)
		db_header_size = Column(Integer)
		bytes_per_sample = Column(Integer)
		db_count = Column(Integer)
		full_blocks = Column(Integer)
		db_size = Column(Integer)
		db_sample_count = Column(Integer)
		frq_bands = Column(Integer)
		db_spec_count = Column(Integer)
		compression_frq = Column(Integer)
		compression_time = Column(Integer)
		avg_time = Column(Integer)
		avg_frq = Column(Integer)
		spec_duration = Column(Float)
		frq_per_band = Column(Float)
		sample_count = Column(Integer)
		spec_count = Column(Integer)
		adc_type = Column(Integer) # TODO this is an ENUM in buffer_parser
		bit_resolution = Column(Integer)
		fft_log_shift = Column(Integer)























