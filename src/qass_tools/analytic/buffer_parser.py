import os
from typing import Any
import numpy as np
from enum import IntEnum, auto
from struct import unpack
import math


class HeaderDtype(IntEnum):
    # Enum helper class to mark data types
    INT32 = auto()
    INT64 = auto()
    UINT32 = auto()
    UINT64 = auto()
    FLOAT = auto()
    DOUBLE = auto()


class Buffer:
    class DATAMODE(IntEnum):
        DATAMODE_UNDEF = -1,
        # Es wird nur ein Zähler übertragen, der im DSP Modul generiert wird
        DATAMODE_COUNTER_UNUSED = 0
        DATAMODE_SIGNAL = auto()  # Es werden die reinen Signaldaten gemessen und übertragen
        # Die FFT wird in der Hardware durchgeführt und das Ergebnis als FFT Daten übertragen
        DATAMODE_FFT = auto()
        DATAMODE_PLOT = auto()  # 2 dimensionale Graph Daten (war INTERLEAVED, das wird nicht mehr genutzt, taucht aber im kernelmodul als Define für DATAMODES noch auf
        # Datenmodus, der nur in importierten oder künstlichen Buffern auftritt
        DATAMODE_OTHER = auto()
        # Datamode is video (This means file is not a normal buffer, but simply a video file)
        DATAMODE_VIDEO = auto()

        DATAMODE_COUNT = auto()

    class DATATYPE(IntEnum):  # Kompressionsmethoden oder auch Buffertypen
        COMP_INVALID = -2,
        COMP_UNDEF = -1,
        COMP_RAW = 0  # Die reinen unkomprimierten Rohdaten, sowie sie aus der Hardware kommen
        # Datenreduktion durch einfaches Downsampling (jedes x-te Sample gelangt in den Buffer)
        COMP_DOWNSAMPLE = auto()
        COMP_MAXIMUM = auto()  # Die Maximalwerte von jeweils x Samples gelangen in den Buffer
        # Die Durchschnittswerte über jeweils x Samples gelangen in den Buffer
        COMP_AVERAGE = auto()
        COMP_STD_DEVIATION = auto()  # Die Standardabweichung
        COMP_ENVELOP = auto()  # NOT USED!! Der Buffer stellt eine Hüllkurve dar
        COMP_MOV_AVERAGE = auto()  # Der gleitende Mittelwert über eine Blockgröße von x Samples
        # Die Bufferdaten wurden aus einer externen Quelle, die nicht mit dem Optimizer aufgezeichnet wurden erstellt
        COMP_EXTERN_DATA = auto()
        # Zur Zeit verwendet, um MinMaxObjekt Energy signature buffer zu taggen
        COMP_ANALYZE_OVERVIEW = auto()
        # Der gleitende Mittelwert über eine Blockgröße von x Samples (optimierte Berechnung)
        COMP_MOV_AVERAGE_OPT = auto()
        COMP_COLLECTION = auto()  # Wild zusammengeworfene Datenmasse
        COMP_IMPORT_SIG = auto()  # Importierte Signaldaten
        COMP_SCOPE_RAW = auto()  # Vom Oszilloskop aufgezeichnet
        # Der gleitende Mittelwert (Zeit und Frequenz) über eine Blockgröße von x Samples
        COMP_MOV_AVERAGE_FRQ = auto()
        COMP_SLOPECHANGE = auto()  # Steigungswechsel der Amplituden über die Zeit
        COMP_OTHER = auto()
        COMP_IO_SIGNAL = auto()  # Aufgezeichnete IO Signale
        COMP_ENERGY = auto()  # Die Energie (in erster Linie für DM=ANALOG)
        COMP_AUDIO_RAW = auto()  # Raw Daten, die mit dem Sound Device aufgezeichnet wurden
        # was COMP_OBJECT before. Now it is used for Datamode PLOT. Type will be displayed as Graphname, if set
        COMP_XY_PLOT = auto()
        COMP_SECOND_FFT = auto()
        # Raw Daten vom Audio Device, bei denen es sich um einen Audiokommentar handelt
        COMP_AUDIO_COMMENT = auto()
        # CrackProperties Energy Signatur, kommt in erster Linie von Energieprofilen, die auf Daten der CrackDefinitionen Berechnet wurden
        COMP_CP_ENERGY_SIG = auto()
        # This is a video stream that has been recorded while measuring
        COMP_VID_MEASURE = auto()
        # This is a screen cast video stream, that has been captured while measuring or session recording
        COMP_VID_SCREEN = auto()
        COMP_VID_EXT_LINK = auto()  # This is an extern linked video file
        COMP_ENVELOPE_UPPER = auto()  # NOT_USED!! Obere Hüllfläche
        COMP_ENVELOPE_LOWER = auto()  # NOT_USED! Untere Hüllfläche
        COMP_PATTERN_REFOBJ = auto()  # NOT USED! A Pattern Recognition reference object
        COMP_SIGNIFICANCE = auto()  # Nur starke Änderungen werden aufgezeichnet
        # this is the signed 32 bit version of a significance buffer
        COMP_SIGNIFICANCE_32 = auto()
        # NOT_USED! A mask buffer for a pattern ref object (likely this is a float buffer)
        COMP_PATTERN_MASK = auto()
        COMP_GRADIENT_FRQ = auto()  # Gradient buffer in frequency direction
        # Not realy a datatype but used to create CSV files from source buffer
        COMP_CSV_EXPORT = auto()
        # Die Anzahl der Einträge in der Datatypesliste, kein wirklicher Datentyp
        COMP_COUNT = auto()

    class DATAKIND(IntEnum):  # Zusätzliche Spezifikation des Buffers
        KIND_UNDEF = -1,
        KIND_NONE = 0
        KIND_SENSOR_TEST = auto()  # Sensor Pulse Test Daten
        # Debug Plot Buffer, der die Zeiten für das "freimachen" eines Datenblocks enthält
        KIND_PLOT_FREE_DATABLOCK_TIMING = auto()
        KIND_PATTERN_REF_OBJ_COMPR = auto()
        KIND_PATTERN_REF_OBJ_MASK = auto()
        KIND_PATTERN_REF_OBJ_EXTRA = auto()
        KIND_FREE_6 = auto()
        KIND_FREE_7 = auto()
        DATAKIND_CNT = auto()
        # This datakind is out ouf range. It cannot be stored in bufferId anymore (this is legacy stuff)
        KIND_CAN_NOT_BE_HANDLED = DATAKIND_CNT

        # Werte ab hier zur freien Verwendung (Oft ist das ein Zähler für verschiedene Buffer, die ansonsten den selben FingerPrint hätten)
        KIND_USER = 100

    class ADCTYPE(IntEnum):
        ADC_NOT_USED = 0,
        ADC_LEGACY_14BIT = 0
        ADC_16BIT = auto()
        ADC_24BIT = auto()

    def __init__(self, filepath):
        self.__filepath = filepath
        # uint: read with np.uintc and then cast to python int
        # c double is python float
        import numpy as np
        int(np.uintc())
        self.__keywords = [
            ("qassdata----", HeaderDtype.INT32), ("filevers----", HeaderDtype.INT32),
            ("datavers----", HeaderDtype.INT32), ("savefrom----", HeaderDtype.INT32),
            ("datamode----", HeaderDtype.INT32), ("datatype----", HeaderDtype.INT32),
            ("datakind----", HeaderDtype.INT32), ("framsize----", HeaderDtype.INT32),
            ("smplsize----", HeaderDtype.INT32), ("frqbands----", HeaderDtype.INT32),
            ("db_words----", HeaderDtype.INT32), ("avgtimba----", HeaderDtype.INT32),
            ("avgfrqba----", HeaderDtype.INT32), ("m_u_mask--------",HeaderDtype.UINT64),
            ("b_p_samp----", HeaderDtype.INT32), ("s_p_fram----", HeaderDtype.INT32),
            ("db__size----", HeaderDtype.INT32), ("max_ampl----", HeaderDtype.INT32),
            ("nul_ampl----", HeaderDtype.INT32), ("samplert----", HeaderDtype.INT32),
            ("datarate--------", HeaderDtype.DOUBLE), ("samplefr----", HeaderDtype.INT32),
            ("frqshift----", HeaderDtype.INT32), ("fftovers----", HeaderDtype.INT32),
            ("fftlogsh----", HeaderDtype.INT32), ("fftwinfu----", HeaderDtype.INT32),
            ("dbhdsize----", HeaderDtype.INT32), ("comratio----", HeaderDtype.INT32),
            ("tc__real--------", HeaderDtype.DOUBLE), ("frqratio----", HeaderDtype.INT32),
            ("fc__real--------", HeaderDtype.DOUBLE), ("proj__id--------", HeaderDtype.UINT64),
            ("file__id--------", HeaderDtype.UINT64), ("parentid--------", HeaderDtype.INT64),
            ("proc_cnt----", HeaderDtype.INT32), ("proc_rng----", HeaderDtype.INT32),
            ("proc_sub----", HeaderDtype.INT32), ("poly_cnt----", HeaderDtype.INT32),
            ("polycyid----", HeaderDtype.INT32), ("dumpchan----", HeaderDtype.INT32),
            ("del_lock----", HeaderDtype.INT32), ("proctime----", HeaderDtype.UINT32),
            ("lmodtime----", HeaderDtype.UINT32), ("epoctime--------", HeaderDtype.INT64),
            ("mux_port----", HeaderDtype.INT32), ("pampgain----", HeaderDtype.INT32),
            ("dispgain----", HeaderDtype.INT32), ("linfgain----", HeaderDtype.INT32),
            ("auxpara0----", HeaderDtype.INT32), ("auxpara1----", HeaderDtype.INT32),
            ("auxpara2----", HeaderDtype.INT32), ("auxpara3----", HeaderDtype.INT32),
            ("auxpara4----", HeaderDtype.INT32), ("auxpara5--------", HeaderDtype.INT64),
            ("skipsamp--------", HeaderDtype.INT64), ("skiptime--------", HeaderDtype.INT64),
            ("trunsamp--------", HeaderDtype.INT64), ("truntime--------", HeaderDtype.INT64),
            ("skiplfrq----", HeaderDtype.INT32), ("trunhfrq----", HeaderDtype.INT32),
            ("startfrq----", HeaderDtype.INT32), ("end__frq----", HeaderDtype.INT32),
            ("frqpband--------", HeaderDtype.DOUBLE), ("framedur--------", HeaderDtype.DOUBLE),
            ("frameoff----", HeaderDtype.INT32), ("p__flags----", HeaderDtype.INT32),
            ("realfrqc----", HeaderDtype.INT32), ("sub_data----", HeaderDtype.INT32),
            ("sd_dimen----", HeaderDtype.INT32), ("sd_rsize----", HeaderDtype.INT32),
            ("sd_rsizf--------", HeaderDtype.DOUBLE), ("sd_dsize----", HeaderDtype.INT32),
            ("frqmasks----", HeaderDtype.UINT32), ("frqinmas----", HeaderDtype.UINT32),
            ("eheaderf----", HeaderDtype.UINT32), ("adc_type----", HeaderDtype.INT32),
            ("adbitres----", HeaderDtype.INT32), ("baserate--------", HeaderDtype.INT64),
            ("interpol----", HeaderDtype.INT32), ("dcoffset----", HeaderDtype.INT32),
            ("dispralo----", HeaderDtype.INT32), ("disprahi----", HeaderDtype.INT32),
            ("rngtibeg--------", HeaderDtype.INT64), ("rngtiend--------", HeaderDtype.INT64),
            ("realsoff--------", HeaderDtype.INT64), ("extendid--------", HeaderDtype.UINT64),
            ("sim_mode----", HeaderDtype.INT32), ("partnoid----", HeaderDtype.UINT32),
            ("asc_part----", HeaderDtype.UINT32), ("asc_desc----", HeaderDtype.UINT32),
            ("comments----", HeaderDtype.UINT32), ("sparemem----", HeaderDtype.UINT32),
            ("headsend", None)
        ]

        self.__db_keywords = [
            ("blochead----", HeaderDtype.INT32), ("firstsam--------", HeaderDtype.INT64),
            ("lastsamp--------", HeaderDtype.INT64), ("dbfilled----", HeaderDtype.INT32),
            ("mux_port----", HeaderDtype.INT32), ("pampgain----", HeaderDtype.INT32),
            ("dispgain----", HeaderDtype.INT32), ("io_ports----", HeaderDtype.INT32),
            ("dversion----", HeaderDtype.INT32), ("sine_frq----", HeaderDtype.INT32),
            ("sine_amp----", HeaderDtype.INT32), ("sd_dimen----", HeaderDtype.INT32),
            ("sd_rsize----", HeaderDtype.INT32), ("sd_dsize----", HeaderDtype.INT32),
            ("begin_subdat", HeaderDtype.INT32), ("end___subdat", HeaderDtype.INT32),
            ("blockend", HeaderDtype.INT32)  # datatypes for last three keywords guessed
        ]
        self.__metainfo = {}
        self.__db_headers = {}

    def __enter__(self):
        self.file = open(self.__filepath, 'rb')
        self._parse_header()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def _get_var_chars(self, content, key, val, idx):
        if key in ['asc_desc', 'comments', 'sparemem']:
            d_len = val
            val = content[idx:idx + d_len]
            idx += d_len
        elif key == "begin_subdat":
            end_idx = content.index(b"end___subdat", idx)
            val = content[idx:end_idx]
            idx = end_idx

        return key, val, idx

    def _is_keyword_ascii(self, c):
        return (c >= 95 and c <= 122) or (c >= 48 and c <= 57)

    '''
    Test if given bytearray could be a valid keyword
    Input: bytes testkey
    Return: returns True, if all characters are lower case ASCII or numbers or _
    '''

    def _is_possible_keyword(self, testkey):
        for c in testkey:
            if not self._is_keyword_ascii(c):
                return False
        return True

    def _get_header_val(self, idx, content, keyword):
        key: str
        key, data_type = keyword
        key = key.rstrip("-")
        data_len = len(keyword[0]) - len(key)
        data_type = keyword[1]
        curr_content = content[idx:idx + len(key)]

        # TODO: fill the if structur with the correct unpack method from struct.unpack
        def __read_from_bytes(data_type: str, bytes) -> Any:
            """
            Method to translate byte data into correct python datatypes, with the help of given data type
            """
            val: Any = None
            if data_type == HeaderDtype.INT32:
                val, = unpack("i", bytes)
            elif data_type == HeaderDtype.INT64:
                val, = unpack("q", bytes)
            elif data_type == HeaderDtype.UINT32:
                val, = unpack("I", bytes)
            elif data_type == HeaderDtype.UINT64:
                val, = unpack("Q", bytes)
            elif data_type == HeaderDtype.FLOAT:
                val, = unpack("f", bytes)
            elif data_type == HeaderDtype.DOUBLE:
                val, = unpack("d", bytes)
            elif data_type == None:
                pass
            else:
                val = bytes

            return val

        if curr_content.decode() == key:
            idx += len(key)
            val = None
            if data_len != 0:
                val = __read_from_bytes(
                    data_type, content[idx: idx + data_len])
                #val = int.from_bytes(content[idx: idx + data_len], byteorder='little', signed=True)
            idx += data_len

            return self._get_var_chars(content, key, val, idx)

        return None

    def _read_next_value(self, idx, content, keywords):
        for keyword in keywords:
            res = self._get_header_val(idx, content, keyword)
            if res:
                #key, val, next_idx = res
                return res
        # keyword not found
        current_key = content[idx: idx+8].decode()
        print(
            f'Error: Key word "{current_key}" not supported by buffer_parser')

    def _parse_header(self):
        self.file.seek(0)
        # this should contain the complete header i sugest...
        file_start = self.file.read(4096)
        _, header_size, _ = self._get_header_val(
            0, file_start, self.__keywords[0])

        idx = 0
        while idx < header_size:
            try:
                key, val, idx = self._read_next_value(
                    idx, file_start, self.__keywords)
            except:
                idx += 12  # skip unknown parameter value
                testkey = file_start[idx: idx+8]
                # check if current position contains a possible keyword, otherwise
                # add 4 to idx, because most likely the unknown keyword has a 64bit value
                if not self._is_possible_keyword(testkey):
                    idx += 4

            if key:
                self.__metainfo[key] = val

        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        self.file_size = size

        self.__header_size = header_size
        self.__db_header_size = self.__metainfo["dbhdsize"]
        self.__bytes_per_sample = self.__metainfo["b_p_samp"]
        self.__db_size = self.__metainfo["db__size"]
        self.__frq_bands = self.__metainfo["s_p_fram"]
        self.__db_count = math.ceil(
            (self.file_size - self.__header_size) / (self.__db_size + self.__db_header_size))

    def _log(self, data_arr):
        return self.log(data_arr, self.fft_log_shift, self.ad_bit_resolution)

    def _delog(self, data_arr):
        return self.delog(data_arr, self.fft_log_shift, self.ad_bit_resolution)

    def _get_data(self, specFrom, specTo, frq_bands, conversion: str = None):
        pos_start = specFrom * self.__frq_bands * self.__bytes_per_sample
        pos_end = specTo * self.__frq_bands * self.__bytes_per_sample

        db_start = int(pos_start / self.__db_size)
        db_end = int(pos_end / self.__db_size)

        # The following if clauses check whether the datatype is 2 or 4 bytes long. In case of 4 bytes
        # it checks whether bit 3 is set in p__flags because bit 3 indicates a float buffer.
        
        if self.__bytes_per_sample == 2:
            dtype = np.uint16
        elif self.__bytes_per_sample == 4:
            if (self.__metainfo['p__flags'] & 8) == 0:
                dtype = np.uint32
            else:
                dtype = np.float32
        else:
            raise ValueError("Unknown value for bytes_per_sample")

        np_arrays = []

        for db in range(db_start, db_end + 1):
            if db == db_start:
                start_in_db = pos_start - db_start * self.__db_size
            else:
                start_in_db = 0

            if db == db_end:
                end_in_db = pos_end - db_end * self.__db_size
            else:
                end_in_db = self.__db_size

            block_start_pos_in_file = self.__header_size + \
                db * (self.__db_size + self.__db_header_size)

            start_pos_in_file = block_start_pos_in_file + start_in_db + self.__db_header_size
            read_len = int((end_in_db - start_in_db) / self.__bytes_per_sample)

            if start_pos_in_file + read_len >= self.file_size:
                raise ValueError(
                    "The given indices exceed the buffer file's size.")

            # TODO: We should check the length of actual data in this datablock - especially for the last data block
            # but maybe also for intermediate data blocks - since we do not know if the measuring has been paused

            self.file.seek(start_pos_in_file, os.SEEK_SET)  # seek
            arr = np.fromfile(self.file, dtype=dtype, count=read_len)
            if conversion:
                if conversion == 'delog':
                    if self.fft_log_shift != 0:
                        arr = self.delog(
                            arr, self.fft_log_shift, self.bit_resolution)
                elif conversion == 'log':
                    if self.fft_log_shift == 0:
                        arr = self.log(arr, self.fft_log_shift,
                                       self.bit_resolution)
                else:
                    raise InvalidArgumentError(
                        "The given conversion is unknown")
            np_arrays.append(arr)

        # & 0x3fff
        return np.concatenate(np_arrays).reshape(-1, self.__frq_bands)

    def get_data(self, specFrom=None, specTo=None, conversion: str = None):
        """
        This function provides access to the measurement data in the buffer
        file. The data are retrieved for the range of spectra and stored in a
        numpy array. The data can be logarithmized or not. The datatype of the
        array depends on the type of buffer.

        :param specFrom: First spectrum to be retrieved (default first available spectrum)
        :type specFrom: int, optional
        :param specTo: Last spectrum to be retrieved (default last available spectrum)
        :type specTo: int, optional
        :param conversion: Conversion ('log' or 'delog') of the data.
        :type conversion: string, optional

        :raise InvalidArgumentError: The specFrom value is out of range
        :raise InvalidArgumentError: The specTo value is out of range
        :raise ValueError: The given indices exceed the buffer file's size
        :raise InvalidArgumentError: The given conversion is unknown

        :return: The buffers data
        :rtype: numpy ndarray

        :Example:
            import buffer_parser as bp
            proc = range(1,100,1)
            # path contains the path to a directory containing buffer files
            buff = bp.filter_buffers(path, {'wanted_process': proc , 'datamode': bp.Buffer.DATAMODE.DATAMODE_FFT})
            for buffer in buff:
                buff_file = (buffer.filepath)

            with bp.Buffer(buff_file) as buff:
                spec_start = 0
                spec_end = (buff.db_count -1) * buff.db_spec_count
                print('Spec_end: ' + str(spec_end))
                conv = 'delog'
                data = buff.get_data(spec_start, spec_end, conv)
        """
        if specTo and specTo > self.spec_count:
            raise InvalidArgumentError('specTo is out of range')

        if specFrom and (specFrom < 0 or specFrom > specTo):
            raise InvalidArgumentError('specFrom is out of range')

        if not specFrom:
            specFrom = 0

        if not specTo:
            specTo = self.spec_count

        if self.datamode == self.DATAMODE.DATAMODE_SIGNAL:
            return self._get_data(specFrom, specTo, 1, conversion).reshape(-1)
        else:
            return self._get_data(specFrom, specTo, self.__frq_bands, conversion)
    
    def getArray(self, specFrom=None, specTo=None, delog = True):
        """
        Wrapper function to 'get_data'.
        This function provides access to the measurement data in the buffer
        file. The data are retrieved for the range of spectra and stored in a
        numpy array. The data can be logarithmized or not. The datatype of the
        array depends on the type of buffer.

        :param specFrom: First spectrum to be retrieved (default first available spectrum)
        :type specFrom: int, optional
        :param specTo: Last spectrum to be retrieved (default last available spectrum)
        :type specTo: int, optional
        :param delog: To de-logarithmize the data (default True).
        :type delog: boolean, optional

        :raise InvalidArgumentError: The specFrom value is out of range
        :raise InvalidArgumentError: The specTo value is out of range

        :return: The buffers data
        :rtype: numpy ndarray

        :Example:
            import buffer_parser as bp
            proc = range(1,100,1)
            # path contains the path to a directory containing buffer files
            buff = bp.filter_buffers(path, {'wanted_process': proc , 'datamode': bp.Buffer.DATAMODE.DATAMODE_FFT})
            for buffer in buff:
                buff_file = (buffer.filepath)

            with bp.Buffer(buff_file) as buff:
                spec_start = 0
                spec_end = (buff.db_count -1) * buff.db_spec_count
                print('Spec_end: ' + str(spec_end))
                data = buff.get_array(spec_start, spec_end, True)
        """
        if delog:
            return self.get_data(specFrom, specTo, conversion="delog")
        else:
            return self.get_data(specFrom, specTo, conversion="log")
    
    def getSpecDuration(self):
        """
        Wrapper Function for property spec_duration.

        .. seealso: Property spec_duration
        """
        return self.spec_duration
    
    def _parse_db_header(self, content: bytearray) -> dict:
        db_metainfo = {}

        idx = 0
        while idx < self.__db_header_size:
            key, val, idx = self._read_next_value(
                idx, content, self.__db_keywords)
            if key:
                db_metainfo[key] = val

        return db_metainfo

    def db_header(self, db_idx):
        """
        The data block header contains key words and their corresponding
        values. This information is retrieved and stored in a dictionary. The
        values can be accessed by providing the corresponding key. Please
        ensure that the key exists in the database prior to its use or
        use the get method to access its content.Otherwise this will
        cause a runtime error.
        
        :param db_idx: data block index
        :type db_idx: int

        :raises Value_Error: The data block index is out of range.

        :return: a dictionary with the keywords and values
        :rtype: dictionary
        
        :Example:
            # The index of the first data block is 0
            db_idx = 0
            # Function to retrieve the size of the data block
            def db_size(db_idx)
                db_header_dict = db_header(0)
                return(db_header_dict.get('dbfilled', 0)
        """
        if db_idx > self.__db_count:
            raise ValueError('db_idx is out of bounds')

        if db_idx in self.__db_headers:
            return self.__db_headers[db_idx]

        header_start_pos = self.__header_size + db_idx * \
            (self.__db_size + self.__db_header_size)

        self.file.seek(header_start_pos, os.SEEK_SET)
        db_header_content = self.file.read(self.__db_header_size)
        db_metainfo = self._parse_db_header(db_header_content)
        self.__db_headers[db_idx] = db_metainfo
        return db_metainfo

    def db_header_spec(self, spec: int):
        """
        The method returns the data block header of the data block containing
        the spectrum whose index is provided.
        
        :param spec: The index of a spectrum.
        :type spec: int
        
        :return: The data block header
        :rtype: string (???)
        """
        db_idx = int(spec * self.__frq_bands / self.db_sample_count)
        return self.db_header(db_idx)

    def db_value(self, db_idx: int, key: str):
        """
        Similar to the file header each data block has its own header. This
        method returns the value of the property specified by key in the
        specified data block. The first data block has the index 0.

        :param db_idx: The index of the data block.
        :type db_idx: int
        :param key: The string containing the key word.
        :type key: string

        :return: The data block value for the given key
        :rtype: depending on key (INT32, INT64)
        """
        return self.db_header(db_idx)[key]

    def io_ports(self, db_idx: int, byte: int = None, bit: int = None):
        """
        The state of the io ports is stored in the data blocks. There is a key
        regarding the io ports in the data block header and that is accessed
        with this method. However this location is much to coarse to be used.
        The io port settings which should be used can be found in the sub
        data block.

        :param db_idx: Index of the data block
        :type db_idx: int
        :param byte: Number of io port socket [1, 2, 4] 
        :type byte: int, optional
        :param bit: Number of bit [1, 2, 3, 4, 5, 6, 7, 8]
        :type bit: int, optional

        :raises ValueError: The bit argument requires the byte argument.
        :raises ValueError: The given byte has to be one out of [1, 2, 4].
        :raises ValueError: The given bit is out of range.

        :return: ???
        :rtype: ???
        """
        io_word = ~(self.db_value(db_idx, 'io_ports')) & 0xffffff

        if byte is None and bit is not None:
            raise ValueError('The bit argument requires the byte argument')

        if byte is None:
            return io_word

        if byte == 1:
            io_word = (io_word >> 0) & 0xff
        elif byte == 2:
            io_word = (io_word >> 8) & 0xff
        elif byte == 4:
            io_word = (io_word >> 16) & 0xff
        else:
            raise ValueError('The given byte has to be one out of [1, 2, 4]')

        if bit is None:
            return io_word

        if not 1 <= bit <= 8:
            raise ValueError(f'The given bit is out of range: {bit}')

        return io_word >> (bit - 1) & 1 == 1

    def io_ports_spec(self, spec: int, byte: int, bit: int):
        """
        The state of the io ports is stored in the data blocks. There is a key
        regarding the io ports in the data block header and that is accessed
        with this method. However this location is much to coarse to be used.
        The io port settings which should be used can be found in the sub
        data block.

        :param spec: Index of the spectrum
        :type spec: int
        :param byte: Number of io port socket [1, 2, 4] 
        :type byte: int
        :param bit: Number of bit [1, 2, 3, 4, 5, 6, 7, 8]
        :type bit: int

        :raises ValueError: The bit argument requires the byte argument.
        :raises ValueError: The given byte has to be one out of [1, 2, 4].
        :raises ValueError: The given bit is out of range.

        :return: ???
        :rtype: ???
        """
        db_idx = int(spec * self.__frq_bands / self.db_sample_count)
        return self.io_ports_byte(db_idx, byte, bit)

    def file_size(self):
        """
        The file size of the buffer file. The value is not stored in the header
        but retrieved using the operating system.
        
        :return: file size in bytes
        :rtype: INT32
        """
        return self.file_size

    @property
    def metainfo(self):
        """
        The file header of a buffer file contains numerous key words and
        corresponding values. These key words and values are parsed and
        stored in the metainfo dictionary.
        
        :return: The metainfo dictionary
        :rtype: dictionary
        
        :Example:
        key = 'qassdata'
        def keyword(key)
            return buffer.metainfo[key]

        # The above example leads to a runtime error if the keyword is not a
        # key in the dictionary. It would be better to query this beforehand
        # and to provide a default value, thus:

        def keyword(key):
            if key in buffer.metainfo.keys:
                return buffer.metainfo[key]
            else:
                return default_value

        # or shorter:

        def keyword(key):
            return buffer.metainfo.get(key, default_value)
        """
        return self.__metainfo

    @property
    def filepath(self):
        """
        Returns the complete path to the file.
        
        :return: Path to the file
        :rtype: string
        """
        return self.__filepath

    @property
    def header_size(self):
        """
        Each buffer file has a header. This property provides the size of the
        header in bytes (The usual value is 2000 bytes).

        :return: size in bytes
        :rtype: INT32
        """
        return self.__header_size

    @property
    def process(self):
        """
        The process number
        
        :return: The process number
        :rtype: INT32
        """
        return self.__metainfo["proc_cnt"]

    @property
    def channel(self):
        """
        The channel number
        
        :return: The channel number
        :rtype: INT32
        """
        return self.__metainfo["dumpchan"] + 1

    @property
    def datamode(self):
        """
        The data mode is a constant which specifies what kind of data are in
        the buffer. The most important ones are DATAMODE_FFT and 
        DATAMODE_SIGNAL.
        
        :return: The data mode constant
        :rtype: INT32
        """
        return self.DATAMODE(self.__metainfo["datamode"])

    @property
    def datakind(self):
        """
        The data kind constant is a constant which specifies additional
        buffer specifications.
        
        :return: The data kind constant
        :rtype: INT32
        """
        return self.DATAKIND(self.__metainfo["datakind"])

    @property
    def datatype(self):
        """
        The data type constant is a constant which specifies different
        compression and buffer types. The most important one being
        COMP_RAW.
        
        :return: The data type constant
        :rtype: INT32
        """
        return self.DATATYPE(self.__metainfo["datatype"])

    @property
    def process_time(self):
        """
        Returns the Posix timestamp of creation of the file
        in seconds since Thursday, January 1st 1970.
        
        :return: The timestamp as a number of seconds
        :rtype: UINT32
        """
        return self.__metainfo['proctime']

    @property
    def process_date_time(self):
        from datetime import datetime
        """
        Returns a timestamp of the creation as a string

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'
        :rtype: string
        """
        return datetime.utcfromtimestamp(int(self.__metainfo['proctime'])).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def process_measure_timestamp(self):
        """
        Returns the Posix timestamp at measure start time of process in milliseconds
        If epoctime (measure time) is not available due to older buffer format, -1 is returned

        :return:
        :rtype:
        """
        # is measure timestamp available? If not use creation time
        if 'epoctime' in self.__metainfo:
            return self.__metainfo['epoctime']
        else:
            return -1

    @property
    def process_measure_time_string(self):
        """
        Returns the measure start datetime of process in ISO format

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'
        :rtype: string
        """
        from datetime import datetime
        # is measure timestamp available? If not use creation time
        if 'epoctime' in self.__metainfo:
            tsms = int(self.__metainfo['epoctime'])
        else:
            tsms = self.__metainfo['proctime'] * 1000

        datestr = datetime.utcfromtimestamp(
            tsms // 1000).strftime('%Y-%m-%dT%H:%M:%S.')
        datestr += format(tsms % 1000, "03")
        return datestr

    @property
    def last_modification_time(self):
        """
        Returns the Posix timestamp of last modification of the file
        in seconds since Thursday, January 1st 1970.
        
        :return: The timestamp as a number of seconds
        :rtype: UINT32
        """
        return self.__metainfo['lmodtime']

    @property
    def last_modification_date_time(self):
        from datetime import datetime
        """
        Returns a timestamp of the last modification as a string

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'
        :rtype: string
        """
        return datetime.utcfromtimestamp(int(self.__metainfo['lmodtime'])).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def db_header_size(self):
        """
        Each data block has a header. This property provides the size of the
        data block header in bytes.

        :return: size in bytes
        :rtype: INT32
        """
        return self.__db_header_size

    @property
    def bytes_per_sample(self):
        """
        Number of bytes per sample.
        
        :return: Number of bytes per sample
        :rtype: INT32
        """
        return self.__bytes_per_sample

    @property
    def db_count(self):
        """
        Number of data blocks
        
        :return: Number of data blocks
        :rtype INT32
        """
        return self.__db_count

    @property
    def full_blocks(self):
        """
        All but the last data block are of the same size. In order to
        calculate the number of completely filled data blocks the
        header size is substracted from the file size. This figure is divided
        by the sum of the data block header size and data block size and
        rounded down to the nearest integer.
        
        :return: number of full data blocks
        :rtype: int
        """
        return math.floor((self.file_size - self.__header_size) / (self.__db_header_size + self.__db_size))

    @property
    def db_size(self):
        """
        Returns the size of a completely filled data block in bytes.
        
        :return: Size of a completely filled data block.
        :rtype: int
        """
        return self.__db_size

    @property
    def db_sample_count(self):
        """
        Returns the number of samples in a completely filled data block.
        It is calculated by dividing the data block size by the number of
        bytes per sample.
        
        :return: Number of samples
        :rtype: int
        """
        return math.floor(self.__db_size / self.__bytes_per_sample)

    @property
    def frq_bands(self):
        """
        Each spectrum has a maximum sample number of 512. This is the maximum
        number of frequency bands. This figure decreases with compression along
        the frequency axis. The corresponding key word in the metainfo
        dictionary 's_p_fram' (samples per frame).

        :return: Number of frequency bands
        :rtype: INT32
        """
        return self.__frq_bands

    @property
    def db_spec_count(self):
        """
        The number of spectra within a filled data block. It is calculated by
        dividing the number of samples in a data block by the number of
        frequency bands.

        :return: Number of spectra in a filled data block
        :rtype: int
        """
        return int(self.db_sample_count / self.__frq_bands)

    @property
    def compression_frq(self):
        """
        Property which returns the frequency compression factor.
        
        :return: Frequency compression factor
        :rtype: INT32
        """
        return self.__metainfo["frqratio"]

    @property
    def compression_time(self):
        """
        Property which returns the time compression factor.
        
        :return: Time compression factor
        :rtype: INT32
        """
        return self.__metainfo["comratio"]

    @property
    def avg_time(self):
        """
        Property which returns the moving average factor along the
        time axis.

        :return: Factor of the moving average
        :rtype: INT32
        """
        return self.__metainfo.get("auxpara1", 1)

    @property
    def avg_frq(self):
        """
        Property which returns the moving average factor along the
        frequency axis.
        
        :return: Factor of the moving average
        :rtype: INT32
        """
        return self.__metainfo.get("auxpara2", 1)

    @property
    def spec_duration(self):
        """
        The property returns the time for one spectrum in
        nanoseconds.
        
        :return: Time in nanoseconds
        :rtype: float
        """
        return self.__metainfo["framedur"]

    @property
    def frq_per_band(self):
        """
        The property returns the frequency range per band. The maximum number
        of bands is 512.

        :return: Frequency range in Hertz (Hz) for one band
        :rtype: float
        """
        return self.__metainfo["frqpband"]

    @property
    def sample_count(self):
        """
        The number of samples in the buffer. It is calculated by subtracting
        the header size and the data block size times the number of datablocks
        from the file size. This figure is divided by the bytes per sample to
        obtain the number of samples. The number is cast to an int as the
        division usually results in a float due to an incompletely filled
        final data block.
        
        :return: Number of samples
        :rtype: int
        """
        without_header = self.file_size - self.__header_size
        return int((without_header - self.__db_count * self.__db_header_size) / self.__bytes_per_sample)
    
    def getRealSpecCount(self):
        """
        Wrapper function for the property spec_count.
        The number of spectra within a filled data block. It is calculated by
        dividing the number of samples in a data block by the number of
        frequency bands.
        
        :return: Number of spectra in a filled data block
        :rtype: int
        """
        return self.spec_count

    @property
    def spec_count(self):
        """
        The number of spectra in the buffer. It is calculated by dividing 
        the number of samples by the number of frequency bands.

        :return: number of spectra
        :rtype: int
        """
        return int(self.sample_count / self.__frq_bands)

    @property
    def adc_type(self):
        """
        The type of analog/digital converter. The types are defined in class 
        ADC_TYPE with the most important being ADC_16BIT and ADC_24BIT.

        :return: type defined in class ADC_TYPE
        :rtype: int
        """
        return self.ADCTYPE(self.__metainfo["adc_type"])

    @property
    def bit_resolution(self):
        """
        The bit resolution after the FFT. Caution: this is not the type of
        analog digital converter used. The usual value is 16. If no logarithm
        is applied to the data the value is 32.
        
        :return: The bit resolution in bit
        :rtype: INT32
        """
        return self.__metainfo["adbitres"]

    @property
    def fft_log_shift(self):
        """
        Base of the logarithm applied to the data. Please note that a 1 needs
        to be added to the value.
        
        :return: Base of the logarithm
        :rtype: INT32
        """
        return self.__metainfo["fftlogsh"]

    def spec_to_time_ns(self, spec):
        """
        The method calculates the time since measurement start for a given
        index of a spectrum.
        
        :param spec: The index of a spectrum
        :type spec: int

        :return: time in nanoseconds
        :rtype: float
        """
        return spec * self.spec_duration

    def time_to_spec(self, time_ns):
        """
        The method calculates the index of the nearest spectrum to the time
        given since the start of the measurement.

        :param time_ns: Time elapsed since measurement start in ns.
        :type time_ns: float
        
        :return: index of the spectrum
        :rtype: int
        """
        return int(time_ns / self.spec_duration)

    @staticmethod
    def delog(data_arr, fft_log_shift, ad_bit_resolution):
        """
        Method to de-logarithmize a data array.

        :param data_arr: The data array
        :type data_arr: numpy ndarray
        :param fft_log_shift: 
        :type fft_log_shift: int
        :param ad_bit_resolution: The bit resolution (usually 16)
        :type ad_bit_resolution: int
    
        :return: 
        :rtype: numpy ndarray
        """
        shift = fft_log_shift - 1
        bits = ad_bit_resolution if ad_bit_resolution >= 1 else 16
        bit_res_idx = [14, 16, 24].index(bits)

        # remember negative values:
        negative = data_arr < 0
        np.abs(data_arr, out=data_arr)

        # ensure data_arr to be a floating point array
        data_arr = data_arr.astype(np.double, copy=False)

        shift_offset = [23, 23, 31][bit_res_idx]
        max_amp = 1 << bits

        data_arr = data_arr * (shift_offset - shift) / max_amp + shift

        data_arr = (2**data_arr) - (1 << shift)
        data_arr[negative] *= -1

        return data_arr

    @staticmethod
    def log(data_arr, fft_log_shift, ad_bit_resolution):
        """
        Method to logarithmize a data array.

        :param data_arr:
        :type data_arr: numpy ndarray
        :param fft_log_shift:
        :type fft_log_shift: int
        :param ad_bit_resolution: The bit resolution (usually 16)
        :type ad_bit_resolution: int
    
        :return: 
        :rtype: numpy ndarray
        """
        shift = fft_log_shift - 1
        bits = ad_bit_resolution if ad_bit_resolution >= 1 else 16
        bit_res_idx = [14, 16, 24].index(bits)

        # remember negative values:
        negative = data_arr < 0
        np.abs(data_arr, out=data_arr)

        # ensure data_arr to be a floating point array
        data_arr = data_arr.astype(np.double, copy=False)

        shift_offset = [23, 23, 31][bit_res_idx]
        max_amp = 1 << bits

        data_arr = np.log2(data_arr + (1 << shift)) - shift
        data_arr = data_arr * max_amp / (shift_offset - shift)

        data_arr[negative] *= -1

        return data_arr


def filter_buffers(directory, filters):
    """
    This function is currently part of the buffer parser module but is
    likely to be moved into a repository with tools.
    This function takes a directory with buffer files and a dictionary with
    fiter criteria and returns a list of buffer objects from this
    dictionary which fulfill the filter criteria.

    :param directory: path to a directory with buffer files
    :type string
    :param filters: dictionary with filters
    :type dictionary
 
    :return: A list of buffer objects
    :rtype: list
        
    :Example:
        import buffer_parser as bp
        proc = range(1,100,1)
        # path contains the path to a directory containing buffer files
        buff = bp.filter_buffers(path, {'wanted_process': proc , 'datamode': bp.Buffer.DATAMODE.DATAMODE_FFT})
    """
    from pathlib import Path

    pattern = '*p*'
    if 'process' in filters:
        pattern += str(filters['process'])
    pattern += 'c'

    if 'channel' in filters:
        pattern += str(filters['channel'] - 1)
    else:
        pattern += '*'
    pattern += 'b*'

    buffers = []
    for file in Path(directory).rglob(pattern):
        try:
            with Buffer(file) as buff:
                if 'process' in filters and buff.process != filters['process']:
                    continue
                if 'unwanted_process' in filters and buff.process in filters['unwanted_process']:
                    continue
                if 'wanted_process' in filters and buff.process not in filters['wanted_process']:
                    continue
                if 'channel' in filters and filters['channel'] != buff.channel:
                    continue
                if 'datamode' in filters and filters['datamode'] != buff.datamode:
                    continue
                if 'datakind' in filters and filters['datakind'] != buff.datakind:
                    continue
                if 'datatype' in filters and filters['datatype'] != buff.datatype:
                    continue
                if 'compression_time' in filters and filters['compression_time'] != buff.compression_time:
                    continue
                if 'compression_frq' in filters and filters['compression_frq'] != buff.compression_frq:
                    continue
                if 'avg_time' in filters and filters['avg_time'] != buff.avg_time:
                    continue
                if 'avg_frq' in filters and filters['avg_frq'] != buff.frq_time:
                    continue

                buffers.append(buff)
        except Exception:
            print("filter_buffers could not parse:", file.name)
            pass

    return buffers
