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
from logging import warning
import os
from typing import Any, List, Tuple, Union
import numpy as np
from enum import IntEnum, auto
from struct import unpack
import math
import warnings
import codecs

class InvalidArgumentError(ValueError):
    pass


class HeaderDtype(IntEnum):
    # Enum helper class to mark data types
    INT32 = auto()
    INT64 = auto()
    UINT32 = auto()
    UINT64 = auto()
    FLOAT = auto()
    DOUBLE = auto()
    HEX_TUPLE = auto()


class Buffer:
    class DATAMODE(IntEnum):
        DATAMODE_UNDEF = -1
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
        COMP_INVALID = -2
        COMP_UNDEF = -1
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
        KIND_UNDEF = -1
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
        ADC_NOT_USED = 0
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
            ("streamno----", HeaderDtype.UINT32), ("an4dvers----", HeaderDtype.HEX_TUPLE),
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
        self.__last_spectrum=None
        self.file = open(self.__filepath, 'rb')
        self._parse_header()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def __getstate__(self):
        """
        Return path to buffer file, since this is everything needed to reconstruct a buffer object.
        This function is needed for pickling buffer objects.

        :return: Single-element tuple containing the path to the buffer file.
        :rtype: tuple
        """
        return (self.__filepath, )
    
    def __setstate__(self, state):
        """
        Reconstruct buffer from state, which only contains the path to the buffer file.
        This function is needed for unpickling buffer objects.

        :param state: Single-element tuple containing the path to the buffer file.
        :type state: tuple
        """
        self.__init__(*state)

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
            elif data_type == HeaderDtype.HEX_TUPLE:
                # encode the hex representation into a hex string and convert the strings to integer representations
                hex_string = codecs.encode(bytes, "hex")
                # val contains the reversed order of the hex byte representations as a tuple of integers
                val = tuple(int(hex_string[i:i + 2]) for i in range(0, len(hex_string), 2))[::-1]
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
        warnings.warn(
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

        self._calc_spec_duration()
        self._signalNormalizationFactor()

    def _log(self, data_arr):
        return self.log(data_arr, self.fft_log_shift, self.ad_bit_resolution)

    def _delog(self, data_arr):
        return self.delog(data_arr, self.fft_log_shift, self.ad_bit_resolution)

    def _get_data(self, specFrom, specTo, frq_bands, conversion: str = None):
        pos_start = specFrom * self.__frq_bands * self.__bytes_per_sample
        pos_end = specTo * self.__frq_bands * self.__bytes_per_sample

        db_start = int(pos_start / self.__db_size)
        db_end = math.ceil(pos_end / self.__db_size)

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

        for db in range(db_start, db_end):
            if db == db_start:
                start_in_db = pos_start - db_start * self.__db_size
            else:
                start_in_db = 0

            if db == db_end - 1:
                end_in_db = pos_end - (db_end-1) * self.__db_size
            else:
                end_in_db = self.__db_size

            block_start_pos_in_file = self.__header_size + db * (self.__db_size + self.__db_header_size)

            start_pos_in_file = block_start_pos_in_file + start_in_db + self.__db_header_size
            read_len = int((end_in_db - start_in_db) / self.__bytes_per_sample)

            if start_pos_in_file + read_len > self.file_size:
                raise ValueError("The given indices exceed the buffer file's size.")

            # TODO: We should check the length of actual data in this datablock - especially for the last data block
            # but maybe also for intermediate data blocks - since we do not know if the measuring has been paused

            self.file.seek(start_pos_in_file, os.SEEK_SET)  # seek
            arr = np.fromfile(self.file, dtype=dtype, count=read_len)
            if conversion:
                if conversion == 'delog':
                    if self.fft_log_shift != 0:
                        arr = self.delog(arr, self.fft_log_shift, self.bit_resolution)
                elif conversion == 'log':
                    if self.fft_log_shift == 0:
                        arr = self.log(arr, self.fft_log_shift, self.bit_resolution)
                else:
                    raise InvalidArgumentError("The given conversion is unknown")
            np_arrays.append(arr)

        return np.concatenate(np_arrays).reshape(-1, self.__frq_bands) #& 0x3fff

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

        :raises InvalidArgumentError: The specFrom value is out of range
        :raises InvalidArgumentError: The specTo value is out of range
        :raises ValueError: The given indices exceed the buffer file's size
        :raises InvalidArgumentError: The given conversion is unknown

        :return: The buffers data.
        :rtype: numpy ndarray

        .. code-block:: python
                :linenos:

                import qass.tools.analyzer.buffer_parser as bp
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

    def getArray(self, specFrom=None, specTo=None, delog = None):
        """
        Wrapper function to 'get_data'.
        This function provides access to the measurement data in the buffer
        file. The data are retrieved for the range of spectra and stored in a
        numpy array. The data can be logarithmized or not. The datatype of the
        array depends on the type of buffer.

        :param specFrom: First spectrum to be retrieved (default first available spectrum).
        :type specFrom: int, optional
        :param specTo: Last spectrum to be retrieved (default last available spectrum).
        :type specTo: int, optional
        :param delog: To de-logarithmize the data (default None).
        :type delog: boolean, optional

        :raise InvalidArgumentError: The specFrom value is out of range.
        :raise InvalidArgumentError: The specTo value is out of range.

        :return: The buffers data.
        :rtype: numpy ndarray

        .. code-block:: python
                :linenos:

                import qass.tools.analyzer.buffer_parser as bp
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
        if delog == True:
            return self.get_data(specFrom, specTo, conversion="delog")
        elif delog == False:
            return self.get_data(specFrom, specTo, conversion="log")
        else:
            return self.get_data(specFrom, specTo)

    def getSpecDuration(self):
        """
        Wrapper Function for property spec_duration.

        .. seealso: Property spec_duration
        """
        return self.spec_duration

    def _parse_db_header(self, content: bytearray) -> dict:
        db_metainfo = {}

        if content[0] == 0:
            warnings.warn('empty header content')
            #raise ValueError('empty header content')
            return db_metainfo

        idx = 0
        while idx < self.__db_header_size:
            try:
                read_res = self._read_next_value(idx, content, self.__db_keywords)
                if read_res is None:  # key not found
                    warnings.warn('header parse error')
                    idx+=4
                else:
                    key, val, idx = read_res
                    if key:
                        db_metainfo[key] = val
            except Exception as e:
                raise ValueError('data block header content not parseble')

        return db_metainfo

    def _get_datablock_start_pos(self, db_idx):
        return self.__header_size + db_idx * \
            (self.__db_size + self.__db_header_size)
    
    def _first_sample_of_datablock(self, db_idx):
        return int(db_idx * self.__db_size / self.__bytes_per_sample)
    
    def _first_spec_of_datablock(self, db_idx):
        return int(self._first_sample_of_datablock(db_idx) / self.__frq_bands)
    
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

        .. code block:: python
                :linenos:

                # The index of the first data block is 0
                db_idx = 0
                # Function to retrieve the size of the data block
                def db_size(db_idx):
                    db_header_dict = db_header(0)
                    return(db_header_dict.get('dbfilled', 0))
        """
        if db_idx > self.__db_count:
            raise ValueError('db_idx is out of bounds')

        if db_idx in self.__db_headers:
            return self.__db_headers[db_idx]

        header_start_pos = self._get_datablock_start_pos(db_idx)

        self.file.seek(header_start_pos, os.SEEK_SET)
        db_header_content = self.file.read(self.__db_header_size)
        db_metainfo = self._parse_db_header(db_header_content)
        self.__db_headers[db_idx] = db_metainfo
        return db_metainfo

    def db_header_spec(self, spec: int):
        """
        The method returns the data block header as a dictionary of the data
        block containing the spectrum whose index is provided.

        :param spec: The index of a spectrum.
        :type spec: int

        :return: The data block header with keywords and values.
        :rtype: dictionary

        .. code block:: python
                :linenos:

                # The index of the spectrum is 50
                spec = 50
                # Function to retrieve the size of the data block
                def db_size(spec):
                    db_header_dict = db_header_spec(spec)
                    return(db_header_dict.get('dbfilled', 0))
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

        :return: The data block value for the given key.
        :rtype: int
        """
        return self.db_header(db_idx)[key]

    def io_ports(self, db_idx: int, byte: int = None, bit: int = None):
        """
        Deprecated method!
        This method provides the state of the io ports at the time the
        dateblock (indicated by its number db_idx) is written. It does not
        provide information wether the state of any io port changes within the
        datablock. This method will be replaced by a method which analyses the
        data within the sub data block, which is part of the data block header
        and provides information regarding the state of the io ports at a
        higher accuracy.

        :param db_idx: Index of the data block
        :type db_idx: int
        :param byte: Number of io port socket [1, 2, 4]
        :type byte: int, optional
        :param bit: Number of bit [1, 2, 3, 4, 5, 6, 7, 8]
        :type bit: int, optional

        :raises ValueError: The bit argument requires the byte argument.
        :raises ValueError: The given byte has to be one out of [1, 2, 4].
        :raises ValueError: The given bit is out of range.

        :return: byte with the appropriate bits set as an int
        :rtype: int
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
        Deprecated method!
        This method provides the state of the io ports at the time the
        dateblock (indicated by the spec number within the data block) is
        written. It does not provide information wether the state of any io
        port changes within the datablock. This method will be replaced by a
        method which analyses the data within the sub data block, which is
        part of the data block header and provides information regarding the
        state of the io ports at a higher accuracy.

        :param spec: Index of the spectrum
        :type spec: int
        :param byte: Number of io port socket [1, 2, 4]
        :type byte: int
        :param bit: Number of bit [1, 2, 3, 4, 5, 6, 7, 8]
        :type bit: int

        :raises ValueError: The bit argument requires the byte argument.
        :raises ValueError: The given byte has to be one out of [1, 2, 4].
        :raises ValueError: The given bit is out of range.

        :return: byte with the appropriate bits set as an int
        :rtype: int
        """
        db_idx = int(spec * self.__frq_bands / self.db_sample_count)
        return self.io_ports_byte(db_idx, byte, bit)

    def file_size(self):
        """
        The file size of the buffer file. The value is not stored in the header
        but retrieved using the operating system.

        :return: file size in bytes
        :rtype: int
        """
        return self.file_size

    def _calc_spec_duration(self):
        if 'framedur' in self.__metainfo.keys():
            return

        if self.datamode == self.DATAMODE.DATAMODE_FFT:
            needed_keys = ['fftovers', 'samplefr', 'comratio']
            if any(key not in self.__metainfo for key in needed_keys):
                raise ValueError(f'Keys are missing to calculate the spec_duration. Missing keys: {[key for key in needed_keys if key not in self.__metainfo]}')

            duration=(1e9/((self.__metainfo['samplefr']*(1<<self.__metainfo['fftovers']))/1024))*self.__metainfo['comratio']
            self.__metainfo['framedur']=duration
        elif self.datamode == self.DATAMODE.DATAMODE_SIGNAL:
            needed_keys = ['samplefr', 'comratio']
            if any(key not in self.__metainfo for key in needed_keys):
                raise ValueError(f'Keys are missing to calculate the spec_duration. Missing keys: {[key for key in needed_keys if key not in self.__metainfo]}')

            sample_frq = self.__metainfo['samplefr']
            compression = self.__metainfo['comratio']
            self.__metainfo['framedur']=int(1e9 / sample_frq * compression)

    def _signalNormalizationFactor(self,gain=1):
        """_signalNormalizationFactor calculates a ref_energy factor to derive a normalized energy related to time, frequency and amplitude ranges
        of the buffer. A rectangular signal volume, which's base is the rectangle of one spectrums distance and one frequency band's width
        e.g. (100mV * 82�s * 1525Hz) = 0.012505 V. As the voltage is not squared, the result is close to the square-root of an energy.

        Each amplitude could reach a maximum of 1 Volt, the maximum ADC input voltage.
        Therefore we divide the amplitude with the maximum amplitude number to get it's portion in Volt.
        Then we multiply with the time and frequency square, as we assume the amplitude is constant over the complete square (our best guessing).

        When calculating energies of buffer ranges, we simply summarize the contained amplitudes.
        By multiplying the resulting sum with the ref_energy factor, we achieve the above described calculation of the signals volume.

        The resulting energy should be stable, even if compressing time and frequencies, using oversampling and different ADC ranges.

        sum of amplitudes,
        comparable even if sample rate, oversampling etc. is changing
        param gain,
        usually the amplitude ref is 1.0 equal 100% (eliminates the bit resolution of the buffer)
        could be enhanced with the amplification information of the amplifiers

        :param gain: can reflect changes of the amplification chain, energy is then related where the gain starts (sensor output e.g.), defaults to 1
        :type gain: float, optional
        :return: a factor to multiply with the sums of amplitudes in time-frequency-buffers
        :rtype: float
        """

        self.__norm_factor = 1.0
        if gain == 0.0:
            gain = 1.0

        max_amp = self.max_amplitude_level * gain
        #16 bit=65535, gain=250 => maximum Amp=1V/250=0.004V ~ 4mV
        if max_amp:
            if self.__frq_bands > 1:
                self.__norm_factor = self.frq_per_band * self.spec_duration / 1e9 / max_amp
            else:
                # normFactor = specDuration() / 1e9 / max_amp;
                #//@todo: calculation may be wrong, check it
                self.__norm_factor = 1.0

        else:
            max_amp=2<<16
            max_amp*=gain
            self.__norm_factor=self.frq_per_band * self.spec_duration / 1e9 / max_amp

        return self.__norm_factor

    def block_infos(self, columns: List[str]=['preamp_gain', 'mux_port', 'measure_positions', 'inputs', 'outputs'], changes_only: bool=False, fast_jump: bool = True):
        """block_infos iterates through all memory blocks of a buffer file (typically one MB) and fetches the subdata information
        each memory block has one set of metadata but e.g. 65 subdata entries for raw files
        or more than 2000 entries for a 32 times compressed file,
        where each entry contains meta information about a small time frame (15 spectrums in raw fft files)

        :param columns: List of columns that should be in the result_array.
        You can define the order of the columns here.
        Possible column names are: ['preamp_gain', 'mux_port', 'measure_positions', 'inputs', 'outputs', 'times', 'index', 'spectrums']
        :type columns: List[str]
        
        :param changes_only: Flag to enable a summarized output. If True the output does not contain all entries but only entries where the data columns changed.
        In the current implementation the memory consumption does not change here -> in both cases the array is first completely built.
        Defaults to False.
        :type changes_only: bool
        
        :param fast_jump: If True the function uses seeking in the file instead of parsing every single datablock header.
        The offsets are investigated for the first datablock header and simply applied for all other datablock headers.
        Seeking is usually faster than parsing the datablock headers if they are not already in the cache.
        If the datablock headers are already cached this flag has no effect.
        Defaults to true.
        :type fast_jump: bool

        :return: header_infos, an array containing (spec_index), (index), (times), preamp_gain, mux_port, measure_position, 24bit input, 16bit output, (times), (index), (spec_index)
        :rtype: numpy array of int64, if times are included otherwise int32
        """


        data_columns = ['preamp_gain', 'mux_port', 'measure_positions', 'inputs', 'outputs']
        data_columns_indices = [0, 1, 2, 3, 5]  # positions in subdat block
        index_columns = ['times', 'index', 'spectrums']

        allowed_columns = data_columns + index_columns

        for col in columns:
            if col not in allowed_columns:
                raise InvalidArgumentError(f"Column {col} is not a valid column name. Valid columns are: {allowed_columns}")
            if columns.count(col) > 1:
                raise InvalidArgumentError(f"Column {col} is used multiple times. This is not allowed.")

        if changes_only:
            if not any(col in index_columns for col in columns):
                raise InvalidArgumentError(f"If you use the changes_only option you need to declare at least one index column. Otherwise the results would have no connection.")

        #interpreting the entries as int32 makes most sense
        last_sample=0
        #old header size was 10+32bit entries
        ds_size=10
        mi=self.db_header(0)
        if 'begin_subdat' not in mi:
            raise ValueError(f'begin_subdat keyword missing in datablock {0} -> caonnot read IO information')

        subdat=np.frombuffer(mi['begin_subdat'],dtype=np.int32)
        #if it is of extended type, we expect a reasonable value here
        mysize=int(subdat[10:11])

        if mysize==80:#the extended data length, additional sizes may occur
            ds_size=20 #again the size in 32bit entries

        entries_before = 0

        if fast_jump:
            db_start_pos = self._get_datablock_start_pos(0)
            self.file.seek(db_start_pos, os.SEEK_SET)
            db_header_content = self.file.read(self.__db_header_size)
            start_mark = b'begin_subdat'
            end_mark = b'end___subdat'
            try:
                subdat_offset_start = db_header_content.index(start_mark) + len(start_mark)
                subdat_offset_end = db_header_content.index(end_mark)
                subdat_length = subdat_offset_end - subdat_offset_start
                subdat_readlen = int(subdat_length / subdat.itemsize)
            except ValueError as e:
                raise ValueError(f"The datablock header seems not to have a subdat block. Reading block info not possibe. {str(e)}")

        samples_per_entry = mi['sd_rsize']/self.bytes_per_sample
        specs_per_entry = samples_per_entry / self.frq_bands
        entries_per_spec = 1/specs_per_entry

        #columns of interest:
        #pgain, mux_port, measure_position, 24bit input (inverted), 16bit output (inverted)
        data_columns_src = []  # column index in the buffers meta info array
        data_columns_dest = []  # column index in the target result_array

        times_col = None
        index_col = None
        specs_col = None

        for idx, col in enumerate(columns):
            if col == 'times':
                times_col = idx
            elif col == 'index':
                index_col = idx
            elif col == 'spectrums':
                specs_col = idx
            elif col in data_columns:
                data_columns_src.append(data_columns_indices[data_columns.index(col)])
                data_columns_dest.append(idx)

        if not data_columns_dest:
            raise InvalidArgumentError('You have to choose at least one data column!')

        # the indices of valid entries in the subdata block are calculated per datablock (checked in Analyzer4D DBgrabber::getSubDataPointer)
        full_datablock_count = (self.spec_count // self.db_spec_count)
        full_datablock_specs = full_datablock_count * self.db_spec_count
        last_nonfull_datablock_specs = self.spec_count % self.db_spec_count
        entry_count = int(full_datablock_specs * min(1, entries_per_spec)) + int(last_nonfull_datablock_specs * min(1, entries_per_spec))
        
        # 64 bit array if index columns are requested, otherwise 32 bit
        arr_type = np.int64 if any((times_col, index_col, specs_col)) is not None else np.int32
        result_arr = np.empty((entry_count, len(columns)), dtype=arr_type)  # allocating the array!

        # loop through the datablocks
        for i in range(self.db_count):
            if fast_jump and not i in self.__db_headers:  # seeking is not faster than using cached datablock headers
                db_start_pos = self._get_datablock_start_pos(i)
                self.file.seek(db_start_pos + subdat_offset_start, os.SEEK_SET)
                entries = np.fromfile(self.file, dtype=np.int32, count=subdat_readlen).reshape(-1, ds_size)
                start_spec = self._first_spec_of_datablock(i)
                end_spec = min(self._first_spec_of_datablock(i+1), self.spec_count)
            else:
                mi=self.db_header(i)
                if 'begin_subdat' not in mi:
                    raise ValueError(f'begin_subdat keyword missing in datablock {i} -> caonnot read IO information')

                subdat=np.frombuffer(mi['begin_subdat'], dtype=np.int32)
                entries=subdat.reshape(-1, ds_size)
                #f_entries=np.empty((0,ds_size),dtype=np.int32)

                #print("mi['sd_rsize']", mi['sd_rsize'])
                samples_per_entry = mi['sd_rsize']/self.bytes_per_sample
                specs_per_entry = samples_per_entry / self.frq_bands
                entries_per_spec = 1/specs_per_entry

                start_spec = int(mi['firstsam'] / self.frq_bands)
                #the end_spec might differ from lastsamp for the last datablock: The real data might be shorter
                end_spec = min(int(mi['lastsamp'] / self.frq_bands), self.spec_count)

            db_spec_count = end_spec - start_spec

            # the number of expected entries might be less than specs for low compressions, but never more than db_spec_count
            entries_expected = int(db_spec_count * min(1, entries_per_spec))

            # max(1, entries_per_spec) because for low compressions we get less than 1 entry per spec -> take every entry
            idxs = np.arange(entries_expected) * max(1, entries_per_spec)
            idxs = idxs.astype(int)

            #filter the entries based on the calculated indexes
            f_entries = entries[idxs]
            
            assert len(f_entries) == entries_expected  # this must be equal - its critical to have a mismatch here!

            # writing columns_of_interest into the result_arr
            result_arr[entries_before:entries_before + len(f_entries), data_columns_dest] = f_entries[:, data_columns_src]

            if times_col is not None:
                start_time = start_spec * self.spec_duration
                end_time = end_spec * self.spec_duration
                times = np.arange(entries_expected, dtype=float)

                # for strong compresssions we get exactly one (and never more than one) entries for each spectrum.
                times *= self.spec_duration / min(1, entries_per_spec)
                times += start_time

                times = times.astype(int)
                result_arr[entries_before:entries_before+len(times), times_col] = times

            if index_col is not None:
                index = np.arange(entries_before, entries_before + entries_expected, dtype=int)
                result_arr[entries_before:entries_before+len(index), index_col] = index

            if specs_col is not None:
                index = np.arange(entries_expected) * max(1, specs_per_entry)
                index = index.astype(int)
                index += start_spec
                result_arr[entries_before:entries_before+len(index), specs_col] = index

            entries_before += entries_expected #len(f_value_list)

        assert entries_before == len(result_arr)  # If this fails we did something wrong when calculating the expected number of entries.

        # Some conversions to ensure readability of the values
        if 'preamp_gain' in columns:
            col = columns.index('preamp_gain')
            result_arr[:, col] = result_arr[:, col] >> 16

        if 'inputs' in columns:
            col = columns.index('inputs')
            result_arr[:, col] = np.bitwise_and(np.bitwise_not(result_arr[:, col]),0xFFFFFF)

        if 'outputs' in columns:
            col = columns.index('outputs')
            result_arr[:, col] = np.bitwise_and(np.bitwise_not(result_arr[:, col]),0xFFFF)

        if changes_only:
            changes_idx = np.concatenate(((True,), np.any(result_arr[1:, data_columns_dest] != result_arr[:-1, data_columns_dest], axis=1)))
            return result_arr[changes_idx]
        else:
            return result_arr

    @property
    def metainfo(self):
        """
        The buffer header properties as a dictionary.

        :return: The metainfo dictionary
        :rtype: dictionary

        .. code-block:: python
                :linenos:

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
        header in bytes (The normal value is 2000 bytes).

        :return: Size in bytes.
        :rtype: int
        """
        return self.__header_size

    @property
    def project_id(self):
        return self.__metainfo["proj__id"]

    @property
    def process(self):
        """
        The process number.

        :return: The process number.
        :rtype: int
        """
        return self.__metainfo["proc_cnt"]

    @property
    def channel(self):
        """
        The channel number used.

        :return: The channel number.
        :rtype: int
        """
        return self.__metainfo["dumpchan"] + 1

    @property
    def streamno(self) -> Union[int, None]:
        """
        The index of a stream of an extra channel.

        Extra channels in the analyzer software can map multiple different data 
        streams to the same channel of the software. This makes them only distuinguishable
        by this property.
        """
        return self.__metainfo.get("streamno", None)

    @property
    def datamode(self):
        """
        The data mode is a constant which specifies what kind of data are in
        the buffer. The most important ones are DATAMODE_FFT and
        DATAMODE_SIGNAL. If you want to obtain the name of the constant, use
        `datamode.name`.

        :return: The data mode constant
        :rtype: enum class defined in :class:`.DATAMODE`
        """
        return self.DATAMODE(self.__metainfo["datamode"])

    @property
    def datakind(self):
        """
        The data kind constant is a constant which provides additional
        buffer specifications. A common value often is
        KIND_UNDEF. If you want to obtain the name of the constant, use
        `datakind.name`.

        :return: The data kind constant.
        :rtype: enum class defined in :class:`.DATAKIND`
        """
        return self.DATAKIND(self.__metainfo["datakind"])

    @property
    def datatype(self):
        """
        The data type constant is a constant which specifies different
        compression and buffer types. The most important one being
        COMP_RAW. If you want to obtain the name of the constant, use
        `datatype.name`.

        :return: The data type constant.
        :rtype: enum class defined in :class:`.DATATYPE`
        """
        return self.DATATYPE(self.__metainfo.get("datatype", -1))

    @property
    def process_time(self):
        """
        Returns the Posix timestamp of creation of the file
        in seconds since Thursday, January 1st 1970. Please note that the
        creation time and measure time might be different.

        :return: The timestamp as a number of seconds.
        :rtype: int
        """
        return self.__metainfo.get('proctime', 0)

    @property
    def process_date_time(self):
        """
        Returns a timestamp of the creation of the file as a string.

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'
        :rtype: string
        """
        from datetime import datetime
        return datetime.utcfromtimestamp(int(self.__metainfo['proctime'])).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def process_measure_timestamp(self):
        """
        Returns the Posix timestamp at measure start of the process in
        milliseconds. If epoctime (measure time) is not available due to an
        older buffer format, the creation time of the buffer is returned.
        Please note: The creation time may not be the same as epoc time.
        This is particularly true for compressed buffers which may be created
        much later!

        :return: The timestamp as a number in seconds.
        :rtype: int
        """
        return self.__metainfo.get('epoctime', self.__metainfo.get('proctime') * 1000)

    @property
    def process_measure_time_string(self):
        """
        Returns the time in ISO format at measure start of the process. If
        epoctime (measure time) is not available due to an older buffer
        format, the creation time of the buffer is returned. Please note:
        The creation time may not be the same as epoc time. This is
        particularly true for compressed buffers which may be created
        much later!

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'.
        :rtype: string
        """
        from datetime import datetime
        tsms = self.__metainfo.get('epoctime', self.__metainfo.get('proctime') * 1000)

        datestr = datetime.utcfromtimestamp(
            tsms // 1000).strftime('%Y-%m-%d %H:%M:%S.')
        datestr += format(tsms % 1000, "03")
        return datestr

    @property
    def last_modification_time(self):
        """
        Returns the Posix timestamp of last modification of the file
        in seconds since Thursday, January 1st 1970.

        :return: The timestamp as a number in seconds.
        :rtype: int
        """
        return self.__metainfo.get('lmodtime', 0)

    @property
    def last_modification_date_time(self):
        from datetime import datetime
        """
        Returns a timestamp of the last modification as a string.

        :return: The timestamp in the form 'yyyy-mm-dd hh:mm:ss'
        :rtype: string
        """
        return datetime.utcfromtimestamp(int(self.__metainfo.get('lmodtime', 0))).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def db_header_size(self):
        """
        Each data block has a header. This property provides the size of the
        data block header in bytes. The sizes of all data block headers are
        equal.

        :return: Size in bytes
        :rtype: int
        """
        return self.__db_header_size

    @property
    def bytes_per_sample(self):
        """
        Number of bytes per sample.

        :return: Number of bytes per sample (usually 2 bytes).
        :rtype: int
        """
        return self.__bytes_per_sample

    @property
    def db_count(self):
        """
        Returns the number of data blocks.

        :return: Number of data blocks.
        :rtype int
        """
        return self.__db_count

    @property
    def full_blocks(self):
        """
        All but the last data block are usually completly filled. In order to
        calculate the number of those data blocks which are completely filled
        the header size of the file is substracted from the file size. This
        figure is divided by the sum of the data block header size and data
        block size and rounded down to the nearest integer.

        :return: Number of full data blocks.
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

        :return: Number of samples.
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

        :return: Number of frequency bands.
        :rtype: int
        """
        return self.__frq_bands

    @property
    def db_spec_count(self):
        """
        The number of spectra within a filled data block. It is calculated by
        dividing the number of samples in a data block by the number of
        frequency bands.

        :return: Number of spectra in a filled data block.
        :rtype: int
        """
        return int(self.db_sample_count / self.__frq_bands)

    @property
    def compression_frq(self):
        """
        Property which returns the frequency compression factor.

        :return: Frequency compression factor.
        :rtype: int
        """
        return self.__metainfo["frqratio"]

    @property
    def compression_time(self):
        """
        Property which returns the time compression factor.

        :return: Time compression factor.
        :rtype: int
        """
        return self.__metainfo["comratio"]

    @property
    def avg_time(self):
        """
        Property which returns the moving average factor along the
        time axis.

        :return: Factor of the moving average.
        :rtype: int
        """
        return self.__metainfo.get("auxpara1", 1)

    @property
    def avg_frq(self):
        """
        Property which returns the moving average factor along the
        frequency axis.

        :return: Factor of the moving average.
        :rtype: int
        """
        return self.__metainfo.get("auxpara2", 1)

    @property
    def spec_duration(self):
        """
        The property returns the time for one spectrum in
        nanoseconds.

        :return: Time in nanoseconds.
        :rtype: float
        """
        return self.__metainfo["framedur"]

    @property
    def frq_start(self):
        """
        The property returns the lowest represented frequency.

        :return: Frequency in Hertz (Hz).
        :rtype: int
        """
        return self.__metainfo["startfrq"] if 'startfrq' in self.__metainfo else 0

    @property
    def frq_end(self):
        """
        The property returns the highest represented frequency.

        :return: Frequency in Hertz (Hz).
        :rtype: int
        """
        return self.__metainfo["end__frq"] if 'end__frq' in self.__metainfo else self.frq_bands * self.frq_per_band

    @property
    def frq_per_band(self):
        """
        The property returns the frequency range per band. The maximum number
        of bands is 512.

        :return: Frequency range in Hertz (Hz) for one band.
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

        :return: Number of spectra in a filled data block.
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
    def last_spec(self):
        if self.__last_spectrum is None:
            last_sample=0

            last_db = self.db_count -1
            mi=self.db_header(last_db)
            if 'lastsamp' not in mi.keys():
                raise ValueError('The datablock header does not contain a key "lastsamp"')

            last_sample=mi['lastsamp']
            self.__last_spectrum=int(last_sample/self.frq_bands)

        return self.__last_spectrum

    @property
    def adc_type(self):
        """
        The type of analog/digital converter. The types are defined in class
        ADC_TYPE with the most important being ADC_16BIT and ADC_24BIT. If
        you want to obtain the name of the constant, use `adc_type.name`.

        :return: The ADCTYPE constant
        :rtype: enum class reference :class:`ADCTYPE`
        """
        return self.ADCTYPE(self.__metainfo["adc_type"])

    @property
    def bit_resolution(self):
        """
        The bit resolution after the FFT. Caution: this is not the type of
        analog digital converter used. The usual value is 16. If no logarithm
        is applied to the data the value is 32.

        :return: The bit resolution.
        :rtype: int
        """
        return self.__metainfo["adbitres"]

    @property
    def fft_log_shift(self):
        """
        Base of the logarithm applied to the data. Please note that a 1 needs
        to be added to the value.

        :return: Base of the logarithm.
        :rtype: int
        """
        return self.__metainfo["fftlogsh"]

    @property
    def max_amplitude_level(self):
        """
        maximum possible amplitude of the buffer, relates to the buffer's dtype
        :rtype: int, float
        """
        return self.__metainfo["max_ampl"]

    @property
    def refEnergy(self):
        """
        refEnergy provides a normalization factor for compressions.
        This makes sums of amplitudes of different compressions comparable to each other.
        See _signalNormalizationFactor for a detailed description.

        :rtype: float
        """
        return self.__norm_factor

    @property
    def ref_energy(self):
        """
        alias for refEnergy()
        """
        return self.refEnergy

    @property
    def preamp_gain(self):
        """
        The preamplifier setting in the multiplexer tab of the Analyzer4D software.

        :rtype: int
        """
        return self.__metainfo["pampgain"]

    @property
    def analyzer_version(self) -> Union[Tuple[int, int, int, int], None]:
        """
        The analyzer4D version as a tuple consisting of (major, minor, patch, ---)
        :rtype: tuple, None
        """
        return self.__metainfo.get("an4dvers", None)

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
        Method to de-logarithmize a data array. Usually when data are measured
        with the Optimizer the data are logarithmized. The problem with
        logarithms is that adding them up constitutes a multiplication of the
        non logarithmized data. So in order to carry out calculations such as
        calculating sums etc. it is crucial to use de-logarithmized data.

        :param data_arr: Array with the logarithmized data.
        :type data_arr: numpy ndarray
        :param fft_log_shift: Base of the logarithm.
        :type fft_log_shift: int
        :param ad_bit_resolution: The bit resolution (usually 16).
        :type ad_bit_resolution: int

        :return: Array with de-logarithmized data.
        :rtype: numpy ndarray of floats
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
        Method to logarithmize a data array. Usually when data are measured
        with the Optimizer the data are logarithmized. The problem with
        logarithms is that adding them up constitutes a multiplication of the
        non logarithmized data. So in order to carry out calculations such as
        calculating sums etc. it is crucial to use de-logarithmized data.
        Sometimes it is necessary to logarithmize data which were artificially
        created or measured without a logarithm.

        :param data_arr: Array with non-logarithmized data.
        :type data_arr: numpy ndarray of floats
        :param fft_log_shift: Base of the logarithm.
        :type fft_log_shift: int
        :param ad_bit_resolution: The bit resolution (usually 16).
        :type ad_bit_resolution: int

        :return: Array with logarithmized data.
        :rtype: numpy ndarray of floats
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

    .. code-block:: python
            :linenos:

            from qass.tools.analyzer import buffer_parser as bp
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
                if 'avg_frq' in filters and filters['avg_frq'] != buff.avg_frq:
                    continue

                buffers.append(buff)
        except Exception:
            warnings.warn(f"filter_buffers could not parse: {file.name}")
            pass

    return buffers

from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import Column, Integer, String, create_engine
import os, sys, traceback, logging


class BufferErrorLogger:
    _Base = declarative_base()

    class BufferError(_Base):
        __tablename__ = "buffer_error"

        buffer_filepath = Column(String, primary_key = True)
        error_type = Column(String, nullable = False)
        error_msg = Column(String, nullable = False)
        stacktrace = Column(String, nullable = False)
        filepath = Column(String, nullable = False)
        function_name = Column(String, nullable = False)
        line_number = Column(Integer, nullable = False)
        line_content = Column(String, nullable = False)


    def __init__(self, session, logger = None, trace_depth_limit = None):
        if logger is None:
            logging.basicConfig(filename = "buffer_error.log")
            logger = logging
        self._logger = logger
        self._session = session
        self._trace_depth_limit = trace_depth_limit

    def log_errors(self, Buffer_cls, buffer_filepath, func, *args, **kwargs):
        """Function calling another function with the instantiated buffer object.
        *args and **kwargs are forwarded to func

        :param Buffer_cls: Buffer class
        :type Buffer_cls: Buffer
        :param buffer_path: The path to the buffer file to be opened
        :type buffer_path: path-like object or string
        :param func: function taking in a Buffer object as the first parameter
        :type func: function
        """
        try:
            with Buffer_cls(buffer_filepath) as b:
                return func(b, *args, **kwargs)
        except Exception as e:
            type_, value, tb = sys.exc_info()
            stack_summary = traceback.extract_tb(tb, self._trace_depth_limit)
            filepath, line_number, function_name, line_content = stack_summary[-1]
            buffer_error = self.BufferError(
                buffer_filepath = buffer_filepath,
                error_type = str(type_),
                error_msg = str(e),
                stacktrace = self.stacksummary_to_string(stack_summary),
                filepath = filepath,
                line_number = line_number,
                function_name = function_name,
                line_content = line_content
            )
            self._logger.error(e)
            self.save_error(buffer_error)

    def save_error(self, buffer_error):
        """Check if an error already exists for the given buffer file and update the existing one

        :param buffer_error: A BufferError object that is to be saved
        :type buffer_error: BufferError
        """
        error = self._session.query(self.BufferError).get(buffer_error.buffer_filepath)
        if error is not None:
            error.error_type = buffer_error.error_type
            error.error_msg = buffer_error.error_msg
            error.stacktrace = buffer_error.stacktrace
            error.filepath = buffer_error.filepath
            error.function_name = buffer_error.function_name
            error.line_number = buffer_error.line_number
            error.line_content = buffer_error.line_content
            self._session.add(error)
        else:
            self._session.add(buffer_error)
        try:
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            self._logger.critical("Error while saving BufferError: %s", e)

    @staticmethod
    def stacksummary_to_string(stacktrace_frame):
        """Joins a stacktrace object into a new line separated string

        :param stacktrace_frame: FrameSummary object of tracebakc.extract_tb()
        :type stacktrace_frame: FrameSummary
        :return: Stack levels separated by \n
        :rtype: str
        """
        return "\n".join(str(s) for s in stacktrace_frame)

    @staticmethod
    def create_session(engine = None, db_url = "sqlite:///buffer_error_db"):
        if engine is None:
            engine = create_engine(db_url)
        session = Session(engine)
        BufferErrorLogger.BufferError.metadata.create_all(engine, 
                            tables = [BufferErrorLogger.BufferError.metadata.tables["buffer_error"]])
        return session
