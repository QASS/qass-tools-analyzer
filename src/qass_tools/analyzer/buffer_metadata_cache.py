import os, re, warnings
from sqlalchemy import Float, create_engine, Column, Integer, String, BigInteger, Identity, Index, Enum
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from pathlib import Path
from enum import auto, IntEnum


__all__ = ["BufferMetadataCache", "BufferMetadata"]
# TODO the enum section can be removed after the buffer_parser moved to this package
class DATAMODE(IntEnum):
    DATAMODE_UNDEF = -1,
    DATAMODE_COUNTER_UNUSED = 0  # Es wird nur ein Zähler übertragen, der im DSP Modul generiert wird
    DATAMODE_SIGNAL = auto()  # Es werden die reinen Signaldaten gemessen und übertragen
    DATAMODE_FFT = auto()  # Die FFT wird in der Hardware durchgeführt und das Ergebnis als FFT Daten übertragen
    DATAMODE_PLOT = auto()  # 2 dimensionale Graph Daten (war INTERLEAVED, das wird nicht mehr genutzt, taucht aber im kernelmodul als Define für DATAMODES noch auf
    DATAMODE_OTHER = auto()  # Datenmodus, der nur in importierten oder künstlichen Buffern auftritt
    DATAMODE_VIDEO = auto()  # Datamode is video (This means file is not a normal buffer, but simply a video file)

    DATAMODE_COUNT = auto()

class DATATYPE(IntEnum): # Kompressionsmethoden oder auch Buffertypen
    COMP_INVALID = -2,
    COMP_UNDEF = -1,
    COMP_RAW = 0  # Die reinen unkomprimierten Rohdaten, sowie sie aus der Hardware kommen
    COMP_DOWNSAMPLE = auto()  # Datenreduktion durch einfaches Downsampling (jedes x-te Sample gelangt in den Buffer)
    COMP_MAXIMUM = auto()  # Die Maximalwerte von jeweils x Samples gelangen in den Buffer
    COMP_AVERAGE = auto()  # Die Durchschnittswerte über jeweils x Samples gelangen in den Buffer
    COMP_STD_DEVIATION = auto()  # Die Standardabweichung
    COMP_ENVELOP = auto()  # NOT USED!! Der Buffer stellt eine Hüllkurve dar
    COMP_MOV_AVERAGE = auto()  # Der gleitende Mittelwert über eine Blockgröße von x Samples
    COMP_EXTERN_DATA = auto()  # Die Bufferdaten wurden aus einer externen Quelle, die nicht mit dem Optimizer aufgezeichnet wurden erstellt
    COMP_ANALYZE_OVERVIEW = auto()  # Zur Zeit verwendet, um MinMaxObjekt Energy signature buffer zu taggen
    COMP_MOV_AVERAGE_OPT = auto()  # Der gleitende Mittelwert über eine Blockgröße von x Samples (optimierte Berechnung)
    COMP_COLLECTION = auto()  # Wild zusammengeworfene Datenmasse
    COMP_IMPORT_SIG = auto()  # Importierte Signaldaten
    COMP_SCOPE_RAW = auto()  # Vom Oszilloskop aufgezeichnet
    COMP_MOV_AVERAGE_FRQ = auto()  # Der gleitende Mittelwert (Zeit und Frequenz) über eine Blockgröße von x Samples
    COMP_SLOPECHANGE = auto()  # Steigungswechsel der Amplituden über die Zeit
    COMP_OTHER = auto()
    COMP_IO_SIGNAL = auto()  # Aufgezeichnete IO Signale
    COMP_ENERGY = auto()  # Die Energie (in erster Linie für DM=ANALOG)
    COMP_AUDIO_RAW = auto()  # Raw Daten, die mit dem Sound Device aufgezeichnet wurden
    COMP_XY_PLOT = auto()  # was COMP_OBJECT before. Now it is used for Datamode PLOT. Type will be displayed as Graphname, if set
    COMP_SECOND_FFT = auto()
    COMP_AUDIO_COMMENT = auto()  # Raw Daten vom Audio Device, bei denen es sich um einen Audiokommentar handelt
    COMP_CP_ENERGY_SIG = auto()  # CrackProperties Energy Signatur, kommt in erster Linie von Energieprofilen, die auf Daten der CrackDefinitionen Berechnet wurden
    COMP_VID_MEASURE = auto()  # This is a video stream that has been recorded while measuring
    COMP_VID_SCREEN = auto()  # This is a screen cast video stream, that has been captured while measuring or session recording
    COMP_VID_EXT_LINK = auto()  # This is an extern linked video file
    COMP_ENVELOPE_UPPER = auto()  # NOT_USED!! Obere Hüllfläche
    COMP_ENVELOPE_LOWER = auto()  # NOT_USED! Untere Hüllfläche
    COMP_PATTERN_REFOBJ = auto()  # NOT USED! A Pattern Recognition reference object
    COMP_SIGNIFICANCE = auto()  # Nur starke Änderungen werden aufgezeichnet
    COMP_SIGNIFICANCE_32 = auto()  # this is the signed 32 bit version of a significance buffer
    COMP_PATTERN_MASK = auto()  # NOT_USED! A mask buffer for a pattern ref object (likely this is a float buffer)
    COMP_GRADIENT_FRQ = auto()  # Gradient buffer in frequency direction
    COMP_CSV_EXPORT = auto()  # Not realy a datatype but used to create CSV files from source buffer
    COMP_COUNT = auto()  # Die Anzahl der Einträge in der Datatypesliste, kein wirklicher Datentyp

class DATAKIND(IntEnum):  # Zusätzliche Spezifikation des Buffers
    KIND_UNDEF = -1,
    KIND_NONE = 0
    KIND_SENSOR_TEST = auto()  # Sensor Pulse Test Daten
    KIND_PLOT_FREE_DATABLOCK_TIMING = auto()  # Debug Plot Buffer, der die Zeiten für das "freimachen" eines Datenblocks enthält
    KIND_PATTERN_REF_OBJ_COMPR = auto()
    KIND_PATTERN_REF_OBJ_MASK = auto()
    KIND_PATTERN_REF_OBJ_EXTRA = auto()
    KIND_FREE_6 = auto()
    KIND_FREE_7 = auto()
    DATAKIND_CNT = auto()
    KIND_CAN_NOT_BE_HANDLED = DATAKIND_CNT # This datakind is out ouf range. It cannot be stored in bufferId anymore (this is legacy stuff)

    KIND_USER = 100  # Werte ab hier zur freien Verwendung

class ADCTYPE(IntEnum):
    ADC_NOT_USED = 0,
    ADC_LEGACY_14BIT = 0
    ADC_16BIT = auto()
    ADC_24BIT = auto()

__Base = declarative_base()
class BufferMetadata(__Base):
    __tablename__ = "buffer_metadata"
    properties = ("id", "projectid", "directory_path", "filename", "header_size", "process", "channel", "datamode", "datakind", "datatype", 
                "process_time", "process_date_time", "db_header_size", "bytes_per_sample", "db_count", "full_blocks", "db_size",
                "db_sample_count", "frq_bands", "db_spec_count", "compression_frq", "compression_time", "avg_time",
                "avg_frq", "spec_duration", "frq_per_band", "sample_count", "spec_count", "adc_type", 
                "bit_resolution",
                "fft_log_shift")

    id = Column(Integer, Identity(start = 1), primary_key = True)
    projectid = Column(Integer)
    directory_path = Column(String, nullable = False, index = True)
    filename = Column(String, nullable = False)
    header_size = Column(Integer)
    process = Column(Integer)
    channel = Column(Integer, index = True)
    datamode = Column(Enum(DATAMODE)) # TODO this is an ENUM in buffer_parser
    datakind = Column(Enum(DATAKIND)) # TODO this is an ENUM in buffer_parser
    datatype = Column(Enum(DATATYPE)) # TODO this is an ENUM in buffer_parser
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
    adc_type = Column(Enum(ADCTYPE)) # TODO this is an ENUM in buffer_parser
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

    def __init__(self, session, Buffer_cls = None): # 		
        self._db = session
        self.Buffer_cls = Buffer_cls

    def synchronize_directory(self, *paths, sync_subdirectories = True, regex_pattern = "^[a-zA-Z0-9_./]*[p][0-9]*[c][0-9a-zA-Z]{1}[b]"):
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
            if sync_subdirectories:
                files = (str(file) for file in Path(path).rglob("*p*c?b*") if os.path.isfile(file) and pattern.match(str(file)))
            else:
                files = (str(file) for file in Path(path).glob("*p*c?b*") if os.path.isfile(file) and pattern.match(str(file)))
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
            try:
                with self.Buffer_cls(file) as buffer:
                    buffer_metadata = BufferMetadata.buffer_to_metadata(buffer)
                    self._db.add(buffer_metadata)
            except Exception as e:
                directory_path, filename = self.split_filepath(file)
                self._db.add(BufferMetadata(directory_path = directory_path, filename = filename, opening_error = str(e)))
                warnings.warn(f"One or more Buffers couldn't be opened {file}", UserWarning)
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

