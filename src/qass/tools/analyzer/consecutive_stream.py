from collections import deque
from typing import Union, List

import numpy as np
import numpy.typing as npt

from .buffer_parser import Buffer, DataConversion
from .error import InvalidDataStream


class ConsecutiveStream:
    """
    This class is a collection of data streams that are or were recorded seamlessly
    without any gap between streams.
    Data streams are collected in a FIFO buffer and the class provides an interface
    that allows to index this collection as if it were a single data stream file.

    Parameters
    ----------
    max_streams : int
        The maximum number of streams that is held in the FIFO buffer (minimum = 1)

    Examples
    -------
    >>> from pathlib import Path

    >>> from qass.tools.analyzer.buffer_parser import Buffer
    >>> from qass.tools.analyzer.consecutive_stream import ConsecutiveStream

    >>> file_one = Path("file1") # has 100 specs
    >>> file_two = Path("file2") # has 150 specs
    >>> con_stream = ConsecutiveStream(max_streams=2)
    >>> con_stream.add_stream(Buffer(file_one))
    >>> con_stream.add_stream(Buffer(file_two))
    >>> con_stream.spec_count # yields 250
    >>> con_stream.min_sample_idx # yields 0
    >>> con_stream.max_sample_idx # yields 250
    >>> con_stream.get_data(50, 75)
    yields the range 50 - 75 from the first file
    >>> con_stream.get_data(150, 200)
    yields the range 50 - 100 from the second file
    >>> con_stream.get_data(75, 125)
    yields the range 75 - 100 from the first file
    and the range 0 - 25 from the second file

    Raises
    ------
    InvalidDataStream
         If multiple aggregations or channels are found in the input streams

    Note
    ----
    If `max_streams` < `len(streams)` the first `len(streams) - max_streams` data streams will be discarded.
    """

    def __init__(self, max_streams: int):
        if max_streams < 1:
            raise ValueError("`max_streams` needs to be greater than zero")
        self._max_streams = max_streams
        self._stream_buffer = deque(maxlen=max_streams)
        # stream indices contain global the start index of each stream
        # stream indices are sorted and monotonically increasing
        self._stream_indices = deque(maxlen=max_streams)

    def to_local_idx(self, idx: int) -> tuple[int, int]:
        """
        Convert an global index into the `ConsecutiveStream` into a local idx
        of a specific stream.
        The function returns the local index and the related data stream file
        index that can be used to retrieve the actual stream instance using
        `ConsecutiveStream.get_stream`.

        Raises
        ------
        LookupError
            If the local data stream is not in the FIFO buffer anymore
        IndexError
            If the local idx is too large for the newest stream

        Parameters
        ----------
        idx : int
            The global index into the `ConsecutiveStream`

        Returns
        -------
        tuple
            A tuple of two indices. The first index is a local index into a
            concrete data stream. The second index is the index of the corresponding
            data stream in the FIFO buffer.
        """
        # INFO: This is binary search and runs in O(log n) with n streams
        # We could still optimize this to amortized O(1) if we cache consecutive accesses
        corresponding_stream_idx = np.searchsorted(self._stream_indices, idx)
        # searchsorted gives the sorted position which is before the related stream
        # in the case of equality and behind the stream if the index is larger
        # in the case it is larger we need to subtract 1 from the index to reference
        # the correct stream
        if (
            corresponding_stream_idx == len(self._stream_indices)
            or idx < self._stream_indices[corresponding_stream_idx]
        ):
            corresponding_stream_idx -= 1

        if corresponding_stream_idx == -1:
            raise LookupError(
                f"Stream for global idx: {idx} has already been evicted from the FIFO buffer"
            )
        stream = self._stream_buffer[corresponding_stream_idx]
        local_idx = idx - self._stream_indices[corresponding_stream_idx]
        if local_idx > stream.spec_count:
            raise IndexError(
                f"Local index {local_idx} is too high for last seen stream "
                f"with {stream.spec_count} samples"
            )
        return local_idx, int(corresponding_stream_idx)

    def add_stream(self, stream: Buffer) -> int:
        """
        Add a new data stream to the FIFO buffer and return the start index of
        the new stream

        Raises
        ------
        InvalidDataStream
            If the provided data stream does not match with the streams that are
            already in the FIFO buffer

        Parameters
        ----------
        stream : Buffer
            The data stream with the same aggregation as the data streams already
            in the FIFO buffer

        Returns
        -------
        int
            The global starting index in the `ConsecutiveStream` of the new stream
        """
        with stream:
            pass
        if len(self._stream_buffer) == 0:
            # initialization
            self._stream_buffer.append(stream)
            self._stream_indices.append(0)
            return self._stream_indices[-1]
        try:
            assert stream.spec_duration == self._stream_buffer[-1].spec_duration
            assert stream.channel == self._stream_buffer[-1].channel
            assert stream.frq_bands == self._stream_buffer[-1].frq_bands
            assert stream.compression_time == self._stream_buffer[-1].compression_time
            assert stream.compression_frq == self._stream_buffer[-1].compression_frq
            assert stream.avg_time == self._stream_buffer[-1].avg_time
            assert stream.avg_frq == self._stream_buffer[-1].avg_frq
        except AssertionError:
            raise InvalidDataStream(
                "The provided data stream does not have the correct aggregation"
            )
        self._stream_indices.append(
            self._stream_indices[-1] + self._stream_buffer[-1].spec_count
        )
        self._stream_buffer.append(stream)
        return self._stream_indices[-1]

    def add_streams(self, streams: List[Buffer]) -> List[int]:
        """Add a collection of stream objects at once

        Note
        ----
        If `len(streams) > ConsecutiveStream.max_streams` only the last
        `max_streams` stream objects will be available.

        Parameters
        ----------
        streams : List[Buffer]
            A list of stream objects that are added to the FIFO buffer

        Returns
        -------
        List[int]
            The global start indices of the added streams.
        """
        start_indices = []
        for stream in streams:
            start_indices.append(self.add_stream(stream))
        return start_indices

    def get_data(
        self, from_: int, to: int, conversion: Union[DataConversion, None] = None
    ) -> npt.NDArray:
        """
        Fetch a range of spectra from the data

        Raises
        ------
        ValueError
            If `from_` >= `to`

        Parameters
        ----------
        from_ : int
            Start spectrum for the range (inclusive)
        to : int
            End spectrum for the range (exclusive)
        conversion : DataConversion, optional
            The used conversion method forwarded to the stream object.

        Returns
        -------
        npt.NDArray
            A numpy array containing the spectra (in case the data stream is a spectrogram)
            or the data points (in case the data stream is a signal stream)
        """
        if from_ >= to:
            raise ValueError(f"`from_` must be lower than `to` but got {(from_, to)}")
        local_from, from_stream_idx = self.to_local_idx(from_)
        local_to, to_stream_idx = self.to_local_idx(to)

        from_stream = self._stream_buffer[from_stream_idx]
        to_stream = self._stream_buffer[to_stream_idx]
        if from_stream_idx == to_stream_idx:
            with from_stream:
                return from_stream.get_data(local_from, local_to, conversion=conversion)
        between_data = []
        for stream_idx in range(from_stream_idx + 1, to_stream_idx):
            stream = self._stream_buffer[stream_idx]
            with stream:
                between_data.append(
                    stream.get_data(0, stream.spec_count, conversion=conversion)
                )

        with from_stream, to_stream:
            left = from_stream.get_data(
                local_from, from_stream.spec_count, conversion=conversion
            )
            right = to_stream.get_data(0, local_to, conversion=conversion)
        return np.concatenate((left, *between_data, right))

    def time_to_spec(self, time: int) -> int:
        return int(time / self._stream_buffer[0].spec_duration)

    def get_stream(self, stream_idx: int) -> Buffer:
        """
        Returns the stream at `stream_idx` from the FIFO buffer.
        The `stream_idx` can be fetched with a call to `self.to_local_idx`

        Parameters
        ----------
        stream_idx : int
            Index into the FIFO buffer
        """
        return self._stream_buffer[stream_idx]

    def get_stream_start_idx(self, stream_idx: int) -> int:
        """
        Returns the global start idx of a given `stream_idx`
        in the FIFO buffer

        Parameters
        ----------
        stream_idx : int
            Index into the FIFO buffer
        """
        return self._stream_indices[stream_idx]

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return (
            f"ConsecutiveStream(streams={len(self._stream_buffer)}, "
            f"max_streams={self._max_streams})"
        )

    @property
    def frq_bands(self) -> int:
        return self._stream_buffer[0].frq_bands

    @property
    def spec_duration(self) -> int:
        return self._stream_buffer[0].spec_duration

    @property
    def channel(self) -> int:
        return self._stream_buffer[0].channel

    @property
    def compression_time(self) -> int:
        return self._stream_buffer[0].compression_time

    @property
    def compression_frq(self) -> int:
        return self._stream_buffer[0].compression_frq

    @property
    def avg_time(self) -> int:
        return self._stream_buffer[0].avg_time

    @property
    def avg_frq(self) -> int:
        return self._stream_buffer[0].avg_frq

    @property
    def frq_per_band(self) -> int:
        return self._stream_buffer[0].frq_per_band

    @property
    def ref_energy(self) -> float:
        return self._stream_buffer[0].ref_energy

    @property
    def spec_count(self) -> int:
        """Returns the maximum global sample idx available in the FIFO buffer

        Warning
        -------
        This does not mean that all samples up to this sample are still available
        because some of the data streams might have already been evicted from the
        FIFO buffer.
        """
        return self._stream_indices[-1] + self._stream_buffer[-1].spec_count

    @property
    def min_sample_idx(self) -> int:
        """The minimum sample idx that is still available in the FIFO buffer"""
        return self._stream_indices[0]

    @property
    def max_sample_idx(self) -> int:
        """The maximum sample idx that is available in the FIFO buffer"""
        return self._stream_indices[-1] + self._stream_buffer[-1].spec_count
