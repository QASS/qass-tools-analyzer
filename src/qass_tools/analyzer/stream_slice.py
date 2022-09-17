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
from Analyzer.Core import Buffer_Py_IF
import numpy as np


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

    def __copy__(self):
        new = self.__class__.__new__(self.__class__)
        new.__start_time = self.__start_time
        new.__start_frq = self.__start_frq
        new.__spec_duration = self.__spec_duration
        new.__frq_per_band = self.__frq_per_band
        new.__stream = self.__stream
        new.__arr = self.__arr
        return new

    @property
    def start_spec(self) -> int:
        """Returns the absolute spectrum number of the first spectrum in the slice"""

        return self.__start_time // self.__spec_duration

    @property
    def end_spec(self) -> int:
        """Returns the absolute spectrum number of the last spectrum in the slice"""
        return self.start_spec + len(self.__arr)

    @property
    def start_time(self):
        """
        Returns the point in time in [ns] of the first spectrum in the slice.
        The time is relative to the measurement start.
        """
        return self.__start_time

    @property
    def end_time(self):
        """
        Returns the point in time in [ns] of the last spectrum in the slice.
        The time is relative to the measurement start.
        """
        return self.__start_time + len(self.__arr) * self.__spec_duration

    @property
    def spec_count(self) -> int:
        """Returns the number of spectra in the slice."""
        return self.__arr.shape[0]

    @property
    def frq_per_band(self):
        """Returns the freqeuncy bandwidth of each datapoint in the slice in [Hz]."""
        return self.__frq_per_band

    @property
    def frq_band_count(self) -> int:
        """Returns the number frequency bands in the slice"""
        return self.__arr.shape[1]

    @property
    def start_frequency(self) -> int:
        """Returns the lowest frequency in a spectrum of the slice in [Hz]."""
        return self.__start_frq

    @property
    def end_frequency(self):
        """Returns the lowest frequency in a spectrum of the slice in [Hz]."""
        return self.__start_frq + self.frq_band_count * self.__frq_per_band

    @property
    def data(self) -> np.ndarray:
        """Returns the data of the slice as an numpy array"""
        return self.__arr

    @property
    def time_per_spec(self) -> int:
        return self.__spec_duration
    
    spec_duration = time_per_spec
    ns_per_spec = time_per_spec

    @property
    def times(self) -> np.ndarray:
        """Returns a numpy array with the times of the slice spectra in [ns]"""
        return spec_times()

    def __smooth_frq(self, window_size_bands):
        out_shape = list(self.__arr.shape)
        out_shape[1] += 1
        curve_cumsum = np.empty(out_shape)

        np.cumsum(self.__arr, axis=1, out=curve_cumsum[:, 1:])
        zeros_shape = list(self.__arr.shape)
        zeros_shape[1] = 1
        curve_cumsum[:, 0:1] = np.zeros(zeros_shape)

        return (curve_cumsum[:, window_size_bands:] - curve_cumsum[:, :-window_size_bands]) / window_size_bands

    def smooth_frq(self, window_size_bands: int):
        new = self.__copy__()
        new.__arr = new.__smooth_frq(window_size_bands)
        
        new.__start_frq += window_size_bands / 2 * self.__frq_per_band
        return new

    def __smooth_time(self, window_size_specs):
        out_shape = list(self.__arr.shape)
        out_shape[0] += 1
        curve_cumsum = np.empty(out_shape)
        
        np.cumsum(self.__arr, axis=0, out=curve_cumsum[1:])
        zeros_shape = list(self.__arr.shape)
        zeros_shape[0] = 1
        curve_cumsum[0] = np.zeros(zeros_shape)
        
        return (curve_cumsum[window_size_specs:] - curve_cumsum[:-window_size_specs]) / window_size_specs

    def smooth_time(self, window_size_specs: int):
        new = self.__copy__()
        new.__arr = new.__smooth_time(window_size_specs)
        new.__start_time += window_size_specs / 2 * self.__spec_duration
        return new

    def compress_frq(self, compression: int):
        new = self.__copy__()
        new.__arr = new.__arr[:, ::compression]
        new.__frq_per_band *= compression
        return new

    def compress_time(self, compression: int):
        new = self.__copy__()
        new.__arr = new.__arr[::compression]
        new.__spec_duration *= compression
        return new

    def smooth_compress(self, smooth_time: int=None, compress_time: int=None, smooth_frq: int=None, compress_frq: int=None):
        new = self.__copy__()
        if smooth_time is not None:
            new.__arr = new.__smooth_time(smooth_time)
            new.__start_time += smooth_time / 2 * self.__spec_duration
            
        if compress_time is not None:
            new.__arr = new.__arr[::compress_time]
            new.__spec_duration *= compress_time
        
        if smooth_frq is not None:
            new.__arr = new.__smooth_frq(smooth_frq)
            new.__start_frq += smooth_frq / 2 * self.__frq_per_band
        
        if compress_frq is not None:
            new.__arr = new.__arr[:, ::compress_frq]
            new.__frq_per_band *= compress_frq
        
        return new

    def spec_times(self, specs: np.ndarray = None) -> np.ndarray:
        """
        Returns the times of all spectra in the slice if no specs array is given.
        Otherwise the points in time of the given spectra are returned.
        All times are relative to the measurement start.
        .. note: The times are calculated with the current slices metadata.
            This will also work for spectra which are not part of the slice
            but this might return times which can't be mapped to specs of the original stream.
        
        :param specs: A numpy array with the spectrum numbers to get the points in time for., defaults to None
        :type specs: np.ndarray, optional

        :return: A numpy array with the points in time in [ns].
        :rtype: np.ndarray
        """
        if specs is None:
            return np.arange(self.spec_count) * self.__spec_duration + self.__start_time
        else:
            return specs * self.__spec_duration + self.__start_time
 
    def spec_time(self, spec: int) -> int:
        """
        Returns the point in time relative to the measurement start
        of a given spectrum.

        :param spec: Spectrum to get the point in time to.
        type: int

        :return: Point in time of the given spectrum in [ns].
        :rtype: int
        """
        return spec * self.__spec_duration + self.__start_time
    
    def crop_specs(self, start_spec: int, end_spec: int, relative: bool = True):
        """
        Method to crop the slice in the time range.
        The cropping is based on the given spectrum numbers.
        Returns a new instance of Streamslice with the cropped data.

        :param start_spec: spectrum number the new slice starts with.
        :type start_spec: int

        :param end_spec: spectrum number the new slice ends with.
        :type end_spec: int

        :raises ValueError: if the start_spec or end_spec is not in range of the slice.
            Or the start_spec is greater then the end_spec.

        :return: A StreamSlice object with the cropped data.
        :rtype: StreamSlice
        """
        if not relative:
            start_spec -= self.start_spec
            end_spec -= self.start_spec

        if not (0 <= start_spec <= len(self.__arr)):
            raise ValueError(f"start_spec is out of range: {start_spec} ({len(self.__arr)})")
        if not (0 <= end_spec <= len(self.__arr)):
            raise ValueError(f"end_spec is out of range: {end_spec} ({len(self.__arr)})")
        if start_spec > end_spec:
            raise ValueError("start_spec is greater than end_spec")

        new = self.__copy__()
        new.__arr = new.__arr[start_spec:end_spec]
        new.__start_time += start_spec * new.__spec_duration
        return new   
    
    def crop_times(self, start_time: int, end_time: int, relative: bool = True):
        """
        Method to crop the slice in time range.
        The cropping is based on given points in time. Unit is [ns].
        Returns a new instance of StreamSlice with the cropped data.
        If relative is set to False the point in time is in relation
        to the start of the measurement. Otherwise in relation to the
        start of the slice.

        :param start_time: A point in time the new slice should begin from in [ns].
        :type start_time: int

        :param end_time: A point in time the new slice should end with in [ns].
        :type end_time: int

        :param relative: A bool flag to mark the given points in time as related to
            the begin of the slice.
        :type relative: bool, optional

        :return: A StreamSlice object with the cropped data.
        :rtype: StreamSlice
        """
        if not relative:
            start_time -= self.__start_time
            end_time -= self.__start_time

        try:
            return self.crop_specs(
                int(start_time // self.__spec_duration),
                int(end_time // self.__spec_duration)
                )
        
        except ValueError as error:
            raise ValueError(f"The start time {start_time} or end time {end_time} is not valid.") from error
   
    def shift_by_spec(self, shift_specs: int):
        """
        Method to change the time base of a slice.
        This could be necessary for syncing purposes.
        Returns a new instance of StreamSlice with the time base shiftet
        by the number of given shift specs.
        A positive number shifts the time base foreward.
        A negative number shifts the time base backward.
        .. note:
            This doesn't modify the underlying data

        :param shift_specs: A number of spectrums to shift the time base
        :type shift_specs: int

        :return: A StreamSlice object with shifted time base
        :rtype: StreamSlice
        """
        return self.shift_by_time(shift_specs * self.__spec_duration)
    
    def shift_by_time(self, shift_time: float):
        """
        Method to change the time base of a slice.
        This could be necessary for syncing purposes.
        Returns a new instance of StreamSlice with the time base shiftet
        by the number of given given time. The Unit is [ns].
        A positive time shifts the time base forward.
        A negative time shifts the time base backward.
        .. note:
            This doesn't modify the underlying data

        :param shift_time: A time in [ns] to shift the time base.
        :type shift_specs: float

        :return: A StreamSlice object with shifted time base
        :rtype: StreamSlice
        """
        new = self.__copy__()
        new.__start_time += shift_time
        return new

    def __crop_frequency_bands(self, from_band: int = None, to_band: int = None):
        if not from_band:
            from_band = 0
        if not to_band:
            to_band = self.__arr.shape[1]

        if not (0 <= from_band <= self.__arr.shape[1]):
            raise ValueError(f"from_band out of range: {from_band}")
        if not (0 < to_band <= self.__arr.shape[1]):
            raise ValueError(f"to_band out of range: {to_band}")
        
        if from_band > to_band:

            raise ValueError("from_band is greater than to_band")
        
        self.__start_frq += from_band * self.__frq_per_band
        self.__arr = self.__arr[:, from_band:to_band]
    
    def crop_frequency_bands(self, from_band: int = None, to_band: int = None):
        """
        Method to crop the slice in the frequency range.
        The cropping is based on the given frequency band numbers.
        Returns a new instance of Streamslice with the cropped data.
        ..note: The lower bound is inclusive and the upper bound is exclusive.

        :param from_band: lower bound for the frequency bands of the new slice.
        :type from_band: int

        :param to_band: upper bound for the frequency bands of the new slice.
        :type to_band: int

        :return: A StreamSlice object with the cropped data.
        :rtype: StreamSlice
        """

        new = self.__copy__()
        new.__crop_frequency_bands(from_band, to_band)
        return new
    
    def crop_frequency(self, from_frq: int = None, to_frq: int = None):
        """
        Method to crop the slice in the frequency range.
        The cropping is based on the given frequencies. The Unit is [Hz].
        The whole frequency range is inclusive.
        Returns a new instance of Streamslice with the cropped data.

        :param from_frq: frequency in [Hz] the new slice should begin with.
        :type from_frq: int

        :param to_frq: frequency in [Hz] the new slice should end with.
        :type to_frq: int

        :return: A StreamSlice object with the cropped data.
        :rtype: StreamSlice
        """

        if from_frq is None:
            from_band = None
        else:
            from_band = int((from_frq - self.__start_frq) // self.__frq_per_band)
            
        if to_frq is None:
            to_band = None
        else:
            to_band = np.ceil((to_frq - self.__start_frq) // self.__frq_per_band)
        
        return self.crop_frequency_bands(from_band, to_band)
