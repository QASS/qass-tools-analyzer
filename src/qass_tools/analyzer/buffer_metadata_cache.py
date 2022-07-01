import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DATETIME, BOOLEAN
from sqlalchemy.orm import Session, declarative_base

from qass_tools.analytic import buffer_parser as bp
from analyzer.database_model import Base, ProcessBuffer






class BufferMetadataCache:

	def __init__(self, session, *sync_connections): # 		
		self._db = session


	def synchronize(self, *paths):
		for path in paths:
			files = (file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file.endswith("000"))
			subdirectories = [os.path.join(path, directory) for directory in os.listdir(path) if not os.path.isfile(os.path.join(path, directory))]
			unsynchronized_files = self.get_non_synchronized_files(path, files)
			self.synchronize(*subdirectories)


	def get_non_synchronized_files(self, filepath, files):
		"""calculate the difference between the set of files and the set of synchronized files

		:param filepath: full path to the files
		:type filepath: str
		:param files: filenames
		:type files: str
		:return: The set of files that are not synchronized
		"""
		synchronized_buffers = set(buffer.filename for buffer in self._db.query(ProcessBuffer).all())
		unsynchronized_files = set(files).difference(synchronized_buffers)
		return unsynchronized_files
		


	@staticmethod
	def create_session(engine = None, db_url = "sqlite:///buffer_metadata_db"):
		if engine is None:
			engine = create_engine(db_url)
		session = Session(engine)
		Base.metadata.create_all(engine, tables = [Base.metadata.tables["process_buffer"]])
		return session



























