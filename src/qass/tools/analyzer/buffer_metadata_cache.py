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
from typing import Any, Callable
from sqlalchemy import Float, create_engine, Column, Integer, String, BigInteger, Identity, Index, Enum, TypeDecorator, select, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.selectable import Select
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
    """This class acts as a template for buffer files. It's properties represent all available metadata of a buffer file.
    This class is used internally as a database model and can be instantiated to provide a template for a buffer file by
    populating desired properties and passing the object to the cache which will in turn create a query based on this object.
    """
    __tablename__ = "buffer_metadata"
    properties = ("id", "project_id", "directory_path", "filename", "header_size", "process", "channel", "datamode", "datakind", "datatype", 
                "process_time", "process_date_time", "db_header_size", "bytes_per_sample", "db_count", "full_blocks", "db_size",
                "db_sample_count", "frq_bands", "db_spec_count", "compression_frq", "compression_time", "avg_time",
                "avg_frq", "spec_duration", "frq_per_band", "sample_count", "spec_count", "adc_type", 
                "bit_resolution",
                "fft_log_shift")

    id = Column(Integer, Identity(start = 1), primary_key=True)
    project_id = Column(BigInteger, index=True)
    directory_path = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    header_size = Column(Integer)
    process = Column(Integer, index=True)
    channel = Column(Integer, index=True)
    datamode = Column(BufferEnum(Buffer.DATAMODE), index=True) # this is an ENUM in buffer_parser
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
    compression_frq = Column(Integer, index=True)
    compression_time = Column(Integer, index=True)
    avg_time = Column(Integer, index=True)
    avg_frq = Column(Integer, index=True)
    spec_duration = Column(Float)
    frq_per_band = Column(Float)
    sample_count = Column(BigInteger)
    spec_count = Column(BigInteger)
    adc_type = Column(BufferEnum(Buffer.ADCTYPE)) # TODO this is an ENUM in buffer_parser
    bit_resolution = Column(Integer)
    fft_log_shift = Column(Integer)

    opening_error = Column(String, nullable=True)


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

Index("project_id_process_index", BufferMetadata.project_id, BufferMetadata.process)
Index("project_id_process_channel_index", BufferMetadata.project_id, BufferMetadata.process, BufferMetadata.channel)
Index("compression_time_frq_index", BufferMetadata.compression_time, BufferMetadata.compression_frq)
Index("project_id_compression_time_frq_index", BufferMetadata.project_id, BufferMetadata.compression_time, BufferMetadata.compression_frq)

class BufferMetadataCache:
    """This class acts as a Cache for Buffer Metadata. It uses a database session with a buffer_metadata table to map
    metadata to files on the disk. The cache can be queried a lot faster than manually opening a lot of buffer files.
    """
    BufferMetadata = BufferMetadata

    def __init__(self, session=None, Buffer_cls=Buffer, db_url="sqlite:///:memory:"):
        if session is not None:
            warnings.warn('The use of the session parameter is deprecated since version 2.3 and will be removed in two minor versions. Use the db_url keyword instead', DeprecationWarning, stacklevel=2)
            self.engine = session.get_bind()
        else:
            self.engine = create_engine(db_url)
        BufferMetadata.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.Buffer_cls = Buffer_cls


    def synchronize_directory(self, *paths, sync_subdirectories = True, regex_pattern = "^.*[p][0-9]*[c][0-9]{1}[b][0-9]{2}", verbose = 1, delete_stale_entries = False):
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
            unsynchronized_files, synchronized_missing_buffers = self.get_non_synchronized_files(files)
            if delete_stale_entries:
                self.remove_files_from_cache(synchronized_missing_buffers, verbose = verbose)
            self.add_files_to_cache(unsynchronized_files, verbose = verbose)

    def synchronize_database(self, *sync_connections):
        # TODO
        pass

    def get_non_synchronized_files(self, files):
        """calculate the difference between the set of files and the set of synchronized files

        :param files: filenames
        :type files: str
        :return: The set of files that are not synchronized, and the database entries that exist but the file is not present anymore
        """
        file_set = set(files)
        with self.Session() as session:
            synchronized_buffers = set(buffer.filepath for buffer in session.query(self.BufferMetadata).all())
        unsynchronized_files = file_set.difference(synchronized_buffers)
        synchronized_missing_buffers = synchronized_buffers.difference(file_set)
        return unsynchronized_files, synchronized_missing_buffers

    def add_files_to_cache(self, files, verbose=0, batch_size=1000):
        """Add buffer files to the cache by providing the complete filepaths

        :param files: complete filepaths that are added to the cache. The filepath is used with the Buffer class to open a buffer and extract the header information.
        :type files: list, tuple of str
        :param verbose: verbosity level. 0 = no feedback, 1 = progress bar
        :type verbose: int, optional
        """
        with self.Session() as session:
            files = tqdm(files, desc = "Adding Buffers") if verbose > 0 and len(files) > 0 else files
            for i, file in enumerate(files):
                try:
                    with self.Buffer_cls(file) as buffer:
                        buffer_metadata = BufferMetadata.buffer_to_metadata(buffer)
                        session.add(buffer_metadata)
                except Exception as e:
                    directory_path, filename = self.split_filepath(file)
                    session.add(BufferMetadata(directory_path = directory_path, filename = filename, opening_error = str(e)))
                    warnings.warn(f"One or more Buffers couldn't be opened {file}", UserWarning)
                if i % batch_size == 0:
                    session.commit()
            session.commit()

    def remove_files_from_cache(self, files, verbose = 0):
        '''Remove synchronized files from the cache

        :param files: complete filepaths that are present in the cache
        :type files: list, tuple of str 
        :param verbose: verbosity level. 0 = no feedback, 1 = progress bar
        :type verbose: int, optional
        '''
        with self.Session() as session:
            files = tqdm(files, desc = "Removing File Entries") if verbose > 0 and len(files) > 0 else files
            for file in files:
                try:
                    entry = session.query(BufferMetadata).filter_by(filepath = file).one()
                    if not entry:
                        continue
                    session.delete(entry)
                except Exception as e:
                    session.rollback()
                    raise e
            session.commit()

    def _deprecated_get_matching_metadata(self, buffer_metadata: BufferMetadata = None, filter_function: Callable = None,
                                  sort_key: Callable = None):
        if (buffer_metadata is not None):
            q = self.get_buffer_metadata_query(buffer_metadata)
        elif filter_function is not None:
            q = select(BufferMetadata).from_statement(text("SELECT * FROM buffer_metadata"))
        else: raise ValueError("You need to provide either a BufferMetadata object or a filter function, or both")
        with self.Session() as session:
            metadata = list(session.execute(q).scalars())

        if filter_function is not None:
            metadata = [m for m in metadata if filter_function(m)]
        if sort_key is not None:
            metadata.sort(key = sort_key)
        return metadata

    def _get_matching_metadata(self,  query: Select = None):
        with self.Session() as session:
            matching_metadata = session.scalars(query).all()
        return matching_metadata

    def get_matching_metadata(self, buffer_metadata: BufferMetadata = None, filter_function: Callable = None, 
                              sort_key: Callable = None, query: Select = None):
        """Query the cache for all BufferMetadata database entries matching 

        :param query: A sqlalchemy select statement specifying the properties of the BufferMetadata objects
        :type query: Select
        :return: A list with the paths to the buffer files that match the buffer_metadata
        :rtype: list[str]
        """
        if query is not None:
            return self._get_matching_metadata(query)
        warnings.warn("The usage of the parameters buffer_metadata, filter_function, sort_key is deprecated since version 2.3 and will be removed in two minor versions. Use the query parameter instead.", DeprecationWarning, stacklevel=2)
        return self._deprecated_get_matching_metadata(buffer_metadata, filter_function, sort_key)

    def get_matching_files(self, buffer_metadata: BufferMetadata = None, filter_function: Callable = None, 
                              sort_key: Callable = None, query: Select = None):
        """Query the Cache for all files matching the properties that selected by the query object.
        The usage of the buffer_metadata, filter_functions and sort_key is deprecated and will be removed in
        two minor versions. Use the sqlalchemy query parameter instead.

        .. code-block:: python
                :linenos:

                BufferMetadataCache.get_matching_files(
                    select(BM).filter(BM.channel==1, BM.compression_freq==4, BM.process > 100)
                )
                # Returns all buffer filepaths with channel = 1, A frequency compression of 4, 
                # processes above 100 sorted by the process number

        .. code-block:: python
                :linenos:
                ### DEPRECATED ###
                BufferMetadataCache.get_matching_files(
                    buffer_metadata = BufferMetadata(channel=1, compression_frq=4),
                    filter_function = lambda bm: bm.process>100,
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
        :param query: A sqlalchemy select statement specifying the properties of the BufferMetadata objects
        :type query: Select
        :return: A list with the paths to the buffer files that match the buffer_metadata
        :rtype: list[str]
        """
        if any(p is not None for p in (buffer_metadata, filter_function, sort_key)):
            warnings.warn("The usage of the parameters buffer_metadata, filter_function, sort_key is deprecated since version 2.3 and will be removed in two minor versions. Use the query parameter instead.", DeprecationWarning, stacklevel=2)

        matching_metadata = self.get_matching_metadata(buffer_metadata, filter_function, sort_key, query)
        return [m.filepath for m in matching_metadata]

    def get_matching_buffers(self, buffer_metadata: BufferMetadata = None, filter_function: Callable = None, 
                              sort_key: Callable = None, query: Select = None):
        """Calls get_matching_files and converts the result to Buffer objects

        :return: List of Buffer objects
        :rtype: list
        """
        if any(p is not None for p in (buffer_metadata, filter_function, sort_key)):
            warnings.warn("The usage of the parameters buffer_metadata, filter_function, sort_key is deprecated since version 2.3 and will be removed in two minor versions. Use the query parameter instead.", DeprecationWarning, stacklevel=2)

        files = self.get_matching_files(buffer_metadata, filter_function, sort_key, query)
        buffers = []
        for file in files:
            try:
                with self.Buffer_cls(file) as buffer:
                    buffers.append(buffer)
            except Exception as e:
                warnings.warn(f'An error occured while parsing a file header, this file will be skipped: {file}')
        return buffers

    def get_buffer_metadata_query(self, buffer_metadata):
        """Converts a .. py:class:: BufferMetadata object to a complete query. Every property of the object will be converted into
        SQL and returned as a ..py:class:: sqlalchemy.orm.query.FromStatement object

        :param buffer_metadata: The template BufferMetadata object.
        :type buffer_metadata: BufferMetadata
        :return: The sqlalchemy query object
        :rtype: sqlalchemy.orm.query.FromStatement
        """
        q = "SELECT * FROM buffer_metadata WHERE opening_error IS NULL AND "
        for prop in self.BufferMetadata.properties:
            prop_value = getattr(buffer_metadata, prop)
            if prop_value is not None:
                if isinstance(prop_value, str):
                    prop_value = f"'{prop_value}'"
                elif isinstance(prop_value, Enum):
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
        BufferMetadata.metadata.create_all(engine)
        return session


    @staticmethod
    def split_filepath(filepath):
        """Splits a filepath to folder and filename and returns them as a tuple

        :param filepath: _description_
        :type filepath: str
        :return: A tuple containing (directory_path, filename) as strings
        :rtype: tuple(str)
        """
        if "/" in filepath:
            filename = filepath.split("/")[-1]
        elif "\\" in filepath:
            filename = filepath.split("\\")[-1]
        directory_path = filepath[:-len(filename)]
        return directory_path, filename

def get_declarative_base():
    """Getter for the declarative Base that is used by the :py:class:`BufferMetadataCache`.

    :return: declarative base class
    """
    return __Base