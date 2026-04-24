import pytest
import json
import numpy as np
import numpy.typing as npt

from qass.tools.analyzer.testing import MockBuffer
from qass.tools.analyzer.consecutive_stream import ConsecutiveStream


class DataMockBuffer(MockBuffer):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data

    def get_data(self, from_: int, to: int, conversion) -> npt.NDArray:
        return self.data[from_:to]

    @property
    def spec_count(self) -> int:
        return len(self.data)


def test_consecutive_stream(tmp_path):
    """Test that the ConsecutiveStream loads the individual streams
    correctly given the global index"""
    # NOTE: The filepath is just something we provide for the interface
    # It is not actually needed
    frq_bands = 8
    metadata = {
        "frq_bands": frq_bands,
        "spec_duration": 1,
        "channel": 1,
        "ref_normal": 1,
        "compression_time": 1,
        "compression_frq": 1,
        "avg_time": 1,
        "avg_frq": 1,
        "frq_per_band": 1,
    }
    filepath = tmp_path / "metadata.json"
    filepath.write_text(json.dumps(metadata))
    data1 = np.random.randn(10, frq_bands)
    stream_1 = DataMockBuffer(data1, filepath=filepath, **metadata, process=1)
    data2 = np.random.randn(10, frq_bands)
    stream_2 = DataMockBuffer(data2, filepath=filepath, **metadata, process=2)
    data3 = np.random.randn(10, frq_bands)
    stream_3 = DataMockBuffer(data3, filepath=filepath, **metadata, process=3)
    consecutive_stream = ConsecutiveStream(max_streams=2)
    consecutive_stream.add_stream(stream_1)  # type: ignore
    consecutive_stream.add_stream(stream_2)  # type: ignore
    # loading only the first stream should equal to the data of the first stream
    loaded_stream1 = consecutive_stream.get_data(0, stream_1.spec_count)
    assert np.array_equal(data1, loaded_stream1)
    loaded_stream2 = consecutive_stream.get_data(
        stream_1.spec_count,
        stream_1.spec_count + stream_2.spec_count,
    )
    assert np.array_equal(data2, loaded_stream2)

    # here the next stream is needed
    stream_start_idx = consecutive_stream.add_stream(stream_3)  # type: ignore
    assert stream_start_idx == sum([s.spec_count for s in (stream_1, stream_2)])
    loaded_stream3 = consecutive_stream.get_data(
        sum([s.spec_count for s in (stream_1, stream_2)]),
        sum([s.spec_count for s in (stream_1, stream_2, stream_3)]),
    )
    assert np.array_equal(data3, loaded_stream3)


def test_consecutive_stream_over_multiple_streams(tmp_path):
    """In this test the middle stream is only implicitly indexed"""
    frq_bands = 8
    metadata = {
        "frq_bands": frq_bands,
        "spec_duration": 1,
        "channel": 1,
        "ref_normal": 1,
        "compression_time": 1,
        "compression_frq": 1,
        "avg_time": 1,
        "avg_frq": 1,
        "frq_per_band": 1,
    }
    filepath = tmp_path / "metadata.json"
    filepath.write_text(json.dumps(metadata))
    data1 = np.random.randn(10, frq_bands)
    stream_1 = DataMockBuffer(data1, filepath=filepath, **metadata, process=1)
    data2 = np.random.randn(10, frq_bands)
    stream_2 = DataMockBuffer(data2, filepath=filepath, **metadata, process=2)
    data3 = np.random.randn(10, frq_bands)
    stream_3 = DataMockBuffer(data3, filepath=filepath, **metadata, process=3)
    consecutive_stream = ConsecutiveStream(max_streams=3)
    start_indices = consecutive_stream.add_streams([stream_1, stream_2, stream_3])  # type: ignore
    assert start_indices == [0, 10, 20]
    loaded_data = consecutive_stream.get_data(
        0,
        sum([s.spec_count for s in (stream_1, stream_2, stream_3)]),
    )
    assert np.array_equal(loaded_data, np.concatenate((data1, data2, data3)))


def test_single_file(tmp_path):
    frq_bands = 8
    metadata = {
        "frq_bands": frq_bands,
        "spec_duration": 1,
        "channel": 1,
        "ref_normal": 1,
        "compression_time": 1,
        "compression_frq": 1,
        "avg_time": 1,
        "avg_frq": 1,
        "frq_per_band": 1,
    }
    filepath = tmp_path / "metadata.json"
    filepath.write_text(json.dumps(metadata))
    data = np.random.randn(10, frq_bands)
    stream = DataMockBuffer(data, filepath=filepath, **metadata, process=1)
    consecutive_stream = ConsecutiveStream(max_streams=1)
    consecutive_stream.add_stream(stream)  # type: ignore
    for i in range(1, 10):
        assert consecutive_stream.spec_count == stream.spec_count * i
        assert consecutive_stream.min_sample_idx == stream.spec_count * (i - 1)
        assert consecutive_stream.max_sample_idx == stream.spec_count * i
        consecutive_stream.add_stream(stream)  # type: ignore


def test_empty_stream():
    consecutive_stream = ConsecutiveStream(max_streams=2)
    with pytest.raises(LookupError):
        consecutive_stream.get_data(0, 10)
