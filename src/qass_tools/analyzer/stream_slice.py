from Analyzer.Core import Buffer_Py_IF
import numpy as np
from qass_tools.analytic import signaltools


class StreamSlice:
    """
    The class StreamSlice is meant to maintain a slice of QASS Buffer data.
    The class is immutable. All functions that apply changes to the slice return a new object.
    This does not cost much performance since the data array is usually not deep copied.
    """
    
    def __init__(self,
                 stream: Buffer_Py_IF,
                 from_time_ns: int = None,
                 to_time_ns: int = None,
                 from_frq_hz: float = None,
                 to_frq_hz: float = None,
                 delog: bool = False):
        
        self.__spec_duration = stream.getSpecDuration()
        self.__stream = stream
        
        if from_time_ns is None:
            start_spec = 0
        else:
            start_spec = int(from_time_ns // self.__spec_duration)
        
        if not (0 <= start_spec <= stream.getRealSpecCount()):
            raise ValueError("start_spec is out of range")
        
        if to_time_ns is None:
            end_spec = stream.getRealSpecCount()
        else:
            end_spec = int(to_time_ns // self.__spec_duration)
        
        if not (0 <= end_spec <= stream.getRealSpecCount()):
            raise ValueError("end_spec is out of range")
        
        if start_spec > end_spec:
            raise ValueError("start_spec is greater than end_spec")
        
        self.__arr = stream.getArray(start_spec, end_spec, delog=delog)
        
        self.__start_time = start_spec * self.__spec_duration
        self.__start_frq = stream.getLowFrequency()
        
        self.__frq_per_band = stream.getFrequencyPerBand()
        self.__arr.flags.writeable = False
        
        if from_frq_hz is not None:
            from_band = int((from_frq_hz - self.__start_frq) / self.__frq_per_band)
        else:
            from_band = None
        
        if to_frq_hz is not None:
            to_band = int((to_frq_hz - self.__start_frq) / self.__frq_per_band)
        else:
            to_band = None
        
        if from_band or to_band:
            self.__crop_frequency_bands(from_band, to_band)

    def __copy(self):
        new = StreamSlice.__new__(StreamSlice)
        new.__start_time = self.__start_time
        new.__start_frq = self.__start_frq
        new.__spec_duration = self.__spec_duration
        new.__frq_per_band = self.__frq_per_band
        new.__stream = self.__stream
        new.__arr = self.__arr
        return new
    
    @property
    def start_spec(self) -> int:
        return self.__start_time // self.__spec_duration
    
    @property
    def end_spec(self) -> int:
        return self.start_spec + len(self.__arr)
    
    @property
    def start_time(self):
        return self.__start_time
    
    @property
    def end_time(self):
        return self.__start_time + len(self.__arr) * self.__spec_duration
    
    @property
    def spec_count(self):
        return self.__arr.shape[0]
    
    @property
    def frq_per_band(self):
        return self.__frq_per_band
    
    @property
    def frq_band_count(self):
        return self.__arr.shape[1]
    
    @property
    def start_frequency(self):
        return self.__start_frq
    
    @property
    def end_frequency(self):
        return self.__start_frq + self.frq_band_count * self.__frq_per_band
    
    @property
    def data(self):
        return self.__arr
    
    def smooth_frq(self, window_size_bands: int):
        new = self.__copy()
        new.__arr = signaltools.smooth(new.data, window_size_bands, axis=1)
        new.__start_frq += window_size_bands / 2 * self.__frq_per_band
        return new
    
    def smooth_time(self, window_size_specs: int):
        new = self.__copy()
        new.__arr = signaltools.smooth(new.data, window_size_specs, axis=0)
        new.__start_time += window_size_specs / 2 * self.__spec_duration
        return new
    
    def compress_frq(self, compression: int):
        new = self.__copy()
        new.__arr = signaltools.compress(new.data, compression, axis=1)
        new.__frq_per_band *= compression
        return new
    
    def compress_time(self, compression: int):
        new = self.__copy()
        new.__arr = signaltools.compress(new.data, compression, axis=0)
        new.__spec_duration *= compression
        return new
    
    def smooth_compress(self, smooth_time: int=None, compress_time: int=None, smooth_frq: int=None, compress_frq: int=None):
        new = self.__copy()
        if smooth_time is not None:
            new.__arr = signaltools.smooth(new.data, smooth_time, axis=0)
            new.__start_time += smooth_time / 2 * self.__spec_duration
            
        if compress_time is not None:
            new.__arr = signaltools.compress(new.data, compress_time, axis=0)
            new.__spec_duration *= compress_time
        
        if smooth_frq is not None:
            new.__arr = signaltools.smooth(new.data, smooth_frq, axis=1)
            new.__start_frq += smooth_frq / 2 * self.__frq_per_band
        
        if compress_frq is not None:
            new.__arr = signaltools.compress(new.data, compress_frq, axis=1)
            new.__frq_per_band *= compress_frq
        
        return new
    
    def spec_times(self, specs: np.ndarray = None) -> int:
        if specs is None:
            return np.arange(self.spec_count) * self.__spec_duration + self.__start_time
        else:
            return specs * self.__spec_duration + self.__start_time
    
    def spec_time(self, spec: int) -> int:
        return spec * self.__spec_duration + self.__start_time
    
    def crop_specs(self, start_spec, end_spec):
        new = self.__copy()
        if not (0 <= start_spec <= len(new.__arr)):
            raise ValueError(f"start_spec is out of range: {start_spec} ({len(new.__arr)})")
        if not (0 <= end_spec <= len(new.__arr)):
            raise ValueError(f"end_spec is out of range: {end_spec} ({len(new.__arr)})")
        if start_spec > end_spec:
            raise ValueError("start_spec is greater than end_spec")
        
        new.__arr = new.__arr[start_spec:end_spec]
        new.__start_time += start_spec * new.__spec_duration
        return new
    
    def crop_times(self, start_time: int, end_time: int):
        return self.crop_specs(
            int(start_time // self.__spec_duration),
            int(end_time // self.__spec_duration)
        )
    
    def crop_times_abs(self, start_time: int, end_time: int):
        return self.crop_times(start_time - self.__start_time, end_time - self.__start_time)
    
    def shift_by_spec(self, shift_specs: int):
        return self.shift_by_time(shift_specs * self.__spec_duration)
    
    def shift_by_time(self, shift_time: float):
        new = self.__copy()
        new.__start_time += shift_time
        return new

    def __crop_frequency_bands(self, from_band: int = None, to_band: int = None):
        if not (0 <= from_band <= self.__arr.shape[1]):
            raise ValueError(f"from_band out of range: {from_band}")
        if not (0 < to_band <= self.__arr.shape[1]):
            raise ValueError(f"to_band out of range: {to_band}")
        
        if from_band > to_band:
            raise ValueError("from_band is greater than to_band")
        
        self.__start_frq += from_band * self.__frq_per_band
        self.__arr = self.__arr[:, from_band:to_band]
    
    def crop_frequency_bands(self, from_band: int = None, to_band: int = None):
        new = self.__copy()
        new.__crop_frequency_bands(from_band, to_band)
        return new
    
    def crop_frequency(self, from_frq: int = None, to_frq: int = None):
        if from_frq is None:
            from_band = None
        else:
            from_band = int((from_frq - self.__start_frq) // self.__frq_per_band)
            
        if to_frq is None:
            to_frq = None
        else:
            to_band = int((to_frq - self.__start_frq) // self.__frq_per_band)
        
        return self.crop_frequency_bands(from_band, to_band)
