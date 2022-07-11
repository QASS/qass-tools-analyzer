import os, re
from datetime import datetime
from sqlalchemy import Float, create_engine, Column, Integer, String, BigInteger, DATETIME, BOOLEAN, Identity
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from glob import glob


__all__ = ["BufferMetadataCache"]

class BufferMetadataCache:
    """This class acts as a Cache for Buffer Metadata. It uses a database session with a buffer_metadata table to map
    metadata to files on the disk. The cache can be queried a lot faster than manually opening a lot of buffer files.
    """
    def __init__(self, session, Buffer_cls = None): # 		
        self._db = session
        self.Buffer_cls = Buffer_cls

    def synchronize_directory(self, *paths, recursive = True, regex_pattern = "^[a-zA-Z0-9_./]*[p][0-9]*[c][0-9]{1}[b]"):
        """synchronize the buffer files in the given paths with the database matching the regex pattern
        
        :param paths: The absolute paths to the directory
        :type paths: str
        :param recursive: When True synchronize all of the subdirectories recursively, defaults to True
        :type recursive: bool, optional
        :param regex_pattern: The regex pattern validating the buffer naming format
        :type regex_pattern: string, optional
        """
        pattern = re.compile(regex_pattern)
        for path in paths:
            files = (file for file in glob(path, recursive = recursive) if os.path.isfile(file) and pattern.match(file))
            unsynchronized_files = self.get_non_synchronized_files(files)
            self.add_files_to_cache(unsynchronized_files)

    def synchronize_database(self, *sync_connections):
        # TODO
        pass

    def get_non_synchronized_files(self, files):
        """calculate the difference between the set of files and the set of synchronized files

        :param filepath: full path to the files
        :type filepath: str
        :param files: filenames
        :type files: str
        :return: The set of files that are not synchronized
        """
        synchronized_buffers = set(buffer.filepath for buffer in self._db.query(self.BufferMetadata).all())
        unsynchronized_files = set(files).difference(synchronized_buffers)
        return unsynchronized_files

    def add_files_to_cache(self, files):
        for file in files:
            with self.Buffer_cls(file) as buffer:
                buffer_metadata = self.buffer_to_metadata(buffer)
                self._db.add(buffer_metadata)
        self._db.commit()

    def get_matching_files(self, buffer_metadata = None, filter_function = None):
        """Query the Cache for all files matching the properties that are set in the BufferMetadata object

        :param buffer_metadata: A metadata object acting as the filter
        :type buffer_metadata: BufferMetadata
        :return: A list with the paths to the buffer files that match the buffer_metadata
        :rtype: list[str]
        """
        if (buffer_metadata is not None):
            q = "SELECT * FROM buffer_metadata WHERE "
            for prop in self.BufferMetadata.properties:
                prop_value = getattr(buffer_metadata, prop)
                if prop_value is not None:
                    q += f"{prop} = {prop_value} AND "
            q = q[:-4]# prune the last AND
        elif filter_function is not None:
            q = "SELECT * FROM buffer_metadata"
        else: raise ValueError("You need to provide either a BufferMetadata object or a filter function, or both")
        buffers = [self.BufferMetadata(**{prop: value for prop, value in zip(self.BufferMetadata.properties, buffer_result)}) for buffer_result in self._db.execute(q)]
        if filter_function is not None:
            buffers = [buffer for buffer in buffers if filter_function(buffer)]
        return [buffer.filepath for buffer in buffers]


    @staticmethod
    def create_session(engine = None, db_url = "sqlite:///buffer_metadata_db"):
        if engine is None:
            engine = create_engine(db_url)
        session = Session(engine)
        BufferMetadataCache.__Base.metadata.create_all(engine, 
                            tables = [BufferMetadataCache.__Base.metadata.tables["buffer_metadata"]])
        return session


    @staticmethod
    def buffer_to_metadata(buffer):
        """Converts a Buffer object to a BufferMetadata database object by copying all the @properties from the Buffer
        object putting them in the BufferMetadata object

        :param buffer: Buffer object
        :type buffer: buffer_parser.Buffer
        """
        if "/" in buffer.filepath:
            filename = buffer.filepath.split("/")[-1]
        elif "\\" in buffer.filepath:
            filename = buffer.filepath.split("\\")[-1]
        directory_path = buffer.filepath[:-len(filename)]
        buffer_metadata = BufferMetadataCache.BufferMetadata(filename = filename, directory_path = directory_path)
        for prop in BufferMetadataCache.BufferMetadata.properties:
            try: # try to map all the buffer properties and skip on error
                setattr(buffer_metadata, prop, getattr(buffer, prop)) # get the @property method and execute it
            except:
                continue
        return buffer_metadata


    __Base = declarative_base()
    class BufferMetadata(__Base):
        __tablename__ = "buffer_metadata"
        properties = ("id", "projectid", "directory_path", "filename", "header_size", "process", "channel", #"datamode", "datakind", "datatype", 
                    "process_time", "process_date_time", "db_header_size", "bytes_per_sample", "db_count", "full_blocks", "db_size",
                    "db_sample_count", "frq_bands", "db_spec_count", "compression_frq", "compression_time", "avg_time",
                    "avg_frq", "spec_duration", "frq_per_band", "sample_count", "spec_count", #"adc_type", 
                    "bit_resolution",
                    "fft_log_shift")

        id = Column(Integer, Identity(start = 1), primary_key = True)
        projectid = Column(Integer)
        directory_path = Column(String, nullable = False)
        filename = Column(String, nullable = False)
        header_size = Column(Integer)
        process = Column(Integer)
        channel = Column(Integer)
        # datamode = Column(Integer) # TODO this is an ENUM in buffer_parser
        # datakind = Column(Integer) # TODO this is an ENUM in buffer_parser
        # datatype = Column(Integer) # TODO this is an ENUM in buffer_parser
        process_time = Column(BigInteger)
        process_date_time = Column(String)
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
        # adc_type = Column(Integer) # TODO this is an ENUM in buffer_parser
        bit_resolution = Column(Integer)
        fft_log_shift = Column(Integer)

        @hybrid_property
        def filepath(self):
            return self.directory_path + self.filename























