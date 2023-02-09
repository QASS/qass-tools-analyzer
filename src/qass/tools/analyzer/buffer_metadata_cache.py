#
# Copyright (c) 2022 QASS GmbH.
# Website: https://qass.net
# Contact: QASS GmbH <info@qass.net>
#
# This file is part of Qass tools 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import os, re, warnings
from sqlalchemy import Float, create_engine, Column, Integer, String, BigInteger, Identity, Index, Enum, TypeDecorator, select, text
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from pathlib import Path
from enum import Enum
from tqdm.auto import tqdm

from .buffer_parser import Buffer


__all__ = ["BufferMetadataCache", "BufferMetadata"]

class BufferEnum(TypeDecorator):
    impl = String
    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.name

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._enumtype[str(value)]


__Base = declarative_base()
class BufferMetadata(__Base):
    __tablename__ = "buffer_metadata"
    properties = ("id", "project_id", "directory_path", "filename", "header_size", "process", "channel", "datamode", "datakind", "datatype", 
                "process_time", "process_date_time", "db_header_size", "bytes_per_sample", "db_count", "full_blocks", "db_size",
                "db_sample_count", "frq_bands", "db_spec_count", "compression_frq", "compression_time", "avg_time",
                "avg_frq", "spec_duration", "frq_per_band", "sample_count", "spec_count", "adc_type", 
                "bit_resolution",
                "fft_log_shift")

    id = Column(Integer, Identity(start = 1), primary_key = True)
    project_id = Column(BigInteger)
    directory_path = Column(String, nullable = False, index = True)
    filename = Column(String, nullable = False)
    header_size = Column(Integer)
    process = Column(Integer)
    channel = Column(Integer, index = True)
    datamode = Column(BufferEnum(Buffer.DATAMODE)) # this is an ENUM in buffer_parser
    datakind = Column(BufferEnum(Buffer.DATAKIND)) # this is an ENUM in buffer_parser
    datatype = Column(BufferEnum(Buffer.DATATYPE)) # this is an ENUM in buffer_parser
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
    compression_frq = Column(Integer, index = True)
    compression_time = Column(Integer, index = True)
    avg_time = Column(Integer, index = True)
    avg_frq = Column(Integer, index = True)
    spec_duration = Column(Float)
    frq_per_band = Column(Float)
    sample_count = Column(Integer)
    spec_count = Column(Integer)
    adc_type = Column(BufferEnum(Buffer.ADCTYPE)) # TODO this is an ENUM in buffer_parser
    bit_resolution = Column(Integer)
    fft_log_shift = Column(Integer)

    opening_error = Column(String, nullable = True)

    Index("channel_compression", "channel", "compression_frq")


    @hybrid_property
    def filepath(self):
        return self.directory_path + self.filename

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
        buffer_metadata = BufferMetadata(filename = filename, directory_path = directory_path)
        for prop in BufferMetadata.properties:
            try: # try to map all the buffer properties and skip on error
                setattr(buffer_metadata, prop, getattr(buffer, prop)) # get the @property method and execute it
            except:
                continue
        return buffer_metadata


class BufferMetadataCache:
    """This class acts as a Cache for Buffer Metadata. It uses a database session with a buffer_metadata table to map
    metadata to files on the disk. The cache can be queried a lot faster than manually opening a lot of buffer files.
    """
    BufferMetadata = BufferMetadata

    def __init__(self, session, Buffer_cls = None):
        self._db = session
        self.Buffer_cls = Buffer_cls


    def synchronize_directory(self, *paths, sync_subdirectories = True, regex_pattern = "^.*[p][0-9]*[c][0-9]{1}[b][0-9]{2}", verbose = 1):
        """synchronize the buffer files in the given paths with the database matching the regex pattern

        :param paths: The absolute paths to the directory
        :type paths: str
        :param recursive: When True synchronize all of the subdirectories recursively, defaults to True
        :type recursive: bool, optional
        :param regex_pattern: The regex pattern validating the buffer naming format
        :type regex_pattern: string, optional
        :param verbose: verbosity level. 0 = no feedback, 1 = progress bar
        :type verbose: int, optional
        """
        pattern = re.compile(regex_pattern)
        for path in paths:
            if sync_subdirectories:
                files = (str(file) for file in Path(path).rglob("*p*c?b*") if os.path.isfile(file) and pattern.match(str(file)))
            else:
                files = (str(file) for file in Path(path).glob("*p*c?b*") if os.path.isfile(file) and pattern.match(str(file)))
            unsynchronized_files = self.get_non_synchronized_files(files)
            self.add_files_to_cache(unsynchronized_files, verbose = verbose)

    def synchronize_database(self, *sync_connections):
        # TODO
        pass

    def get_non_synchronized_files(self, files):
        """calculate the difference between the set of files and the set of synchronized files

        :param filepath: full path to the files
        :type filepath: list, tuple of str
        :param files: filenames
        :type files: str
        :return: The set of files that are not synchronized
        """
        synchronized_buffers = set(buffer.filepath for buffer in self._db.query(self.BufferMetadata).all())
        unsynchronized_files = set(files).difference(synchronized_buffers)
        return unsynchronized_files

    def add_files_to_cache(self, files, verbose = 0):
        """Add buffer files to the cache by providing the complete filepaths

        :param files: complete filepaths that are added to the cache. The filepath is used with the Buffer class to open a buffer and extract the header information.
        :type files: list, tuple of str
        :param verbose: verbosity level. 0 = no feedback, 1 = progress bar
        :type verbose: int, optional
        """
        files = tqdm(files, desc = "Adding Buffers") if verbose > 0 and len(files) > 0 else files
        for file in files:
            try:
                with self.Buffer_cls(file) as buffer:
                    buffer_metadata = BufferMetadata.buffer_to_metadata(buffer)
                    self._db.add(buffer_metadata)
            except Exception as e:
                directory_path, filename = self.split_filepath(file)
                self._db.add(BufferMetadata(directory_path = directory_path, filename = filename, opening_error = str(e)))
                warnings.warn(f"One or more Buffers couldn't be opened {file}", UserWarning)
        self._db.commit()

    def get_matching_files(self, buffer_metadata = None, filter_function = None, sort_key = None):
        """Query the Cache for all files matching the properties that are set in the BufferMetadata object


        .. code-block:: python
                :linenos:

                BufferMetadataCache.get_matching_files(
                    buffer_metadata = BufferMetadata(channel = 1, compression_frq = 4),
                    filter_function = lambda bm: bm.process > 100,
                    sort_key = lambda bm: bm.process)
                # Returns all buffer filepaths with channel = 1, A frequency compression of 4, 
                # processes above 100 sorted by the process number

        :param buffer_metadata: A metadata object acting as the filter. Only buffers matching the attributes of the provided
            BufferMetadata object are selected. This operation is done on the database
        :type buffer_metadata: BufferMetadata
        :param filter_function: A function taking a BufferMetadata object as a parameter returning a boolean.
            This means a conjunction of BufferMetadata attributes.
        :type filter_function: function
        :param sort_key: A function taking a BufferMetadata object as a parameter returning an attribute the objects can be sorted with
        :type sort_key: function
        :return: A list with the paths to the buffer files that match the buffer_metadata
        :rtype: list[str]
        """
        if (buffer_metadata is not None):
            q = self.get_buffer_metadata_query(buffer_metadata)
        elif filter_function is not None:
            q = select(BufferMetadata).from_statement(text("SELECT * FROM buffer_metadata"))
        else: raise ValueError("You need to provide either a BufferMetadata object or a filter function, or both")

        buffers = list(self._db.execute(q).scalars())

        if filter_function is not None:
            buffers = [buffer for buffer in buffers if filter_function(buffer)]
        if sort_key is not None:
            buffers.sort(key = sort_key)
        return [buffer.filepath for buffer in buffers]

    def get_matching_buffers(self, buffer_metadata = None, filter_function = None, sort_key = None):
        """Calls get_matching_files and converts the result to Buffer objects

        :return: List of Buffer objects
        :rtype: list
        """
        files = self.get_matching_files(buffer_metadata = buffer_metadata, filter_function = filter_function, sort_key = sort_key)
        buffers = []
        for file in files:
            with self.Buffer_cls(file) as buffer:
                buffers.append(buffer)
        return buffers

    def get_buffer_metadata_query(self, buffer_metadata):
        q = "SELECT * FROM buffer_metadata WHERE "
        for prop in self.BufferMetadata.properties:
            prop_value = getattr(buffer_metadata, prop)
            if prop_value is not None:
                if isinstance(prop_value, Enum):
                    prop_value = f"'{prop_value.name}'"
                q += f"{prop} = {prop_value} AND "
        q = q[:-4]# prune the last AND
        return select(BufferMetadata).from_statement(text(q))

    @staticmethod
    def create_session(engine = None, db_url = "sqlite:///:memory:"):
        """Create a session and initialize the schema for the BufferMetadataCache. If an engine is provided
        the schema will be expanded by the buffer_metadata table.
        
        :param engine: An instance of a sqlalchemy engine. Typically sqlalchemy.create_engine()
        :type engine:
        :param db_url: The string used to create the engine. This can be a psycopg2, mysql or sqlite3 string. The default will create the database in main memory.
        :type db_url: str
        :return: A sqlalchemy session instance
        :rtype: sqlalchemy.orm.Session
        """
        if engine is None:
            engine = create_engine(db_url)
        session = Session(engine)
        BufferMetadata.metadata.create_all(engine, 
                            tables = [BufferMetadata.metadata.tables["buffer_metadata"]])
        return session



    @staticmethod
    def split_filepath(filepath):
        if "/" in filepath:
            filename = filepath.split("/")[-1]
        elif "\\" in filepath:
            filename = filepath.split("\\")[-1]
        directory_path = filepath[:-len(filename)]
        return directory_path, filename
