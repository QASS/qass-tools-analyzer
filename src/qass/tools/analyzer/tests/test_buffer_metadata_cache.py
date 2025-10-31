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
import json
from uuid import uuid4
from dataclasses import dataclass

from qass.tools.analyzer.buffer_metadata_cache import (
    BufferMetadataCache as BMC,
    BufferMetadata as BM,
)
from qass.tools.analyzer.buffer_parser import Buffer, InvalidFileError
from sqlalchemy import inspect
import pytest

SEED = 42


@dataclass
class MockBuffer:
    """Mock buffer class that is able to parse JSON encoded files.
    All attributes in the JSON are added as fields in the object"""

    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __enter__(self):
        with open(self.filepath, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                raise InvalidFileError("Not a Buffer file")
        for key, value in data.items():
            setattr(self, key, value)

    def __exit__(self, *args, **kwargs):
        pass


@pytest.fixture(scope="function")
def cache():
    """Returns a BufferMetadataCache instance with an in memory database"""
    cache = BMC()
    return cache


def test_session_creation():
    cache = BMC()
    inspector = inspect(cache.engine)
    assert "buffer_metadata" in inspector.get_table_names()


@pytest.mark.parametrize(
    "filepath,data",
    [
        (
            "foo/bar/hoo.000",
            {
                "directory_path": "foo/bar",
                "filename": "hoo.000",
                "project_id": 0,
                "header_hash": uuid4(),
                "header_size": 2000,
                "process": 0,
                "channel": 0,
                "datamode": Buffer.DATAMODE.DATAMODE_FFT,
            },
        ),
        (
            "foo/bar.000",
            {
                "directory_path": "foo",
                "filename": "bar.000",
                "project_id": 2,
                "header_hash": uuid4(),
                "header_size": 4000,
                "process": 1234,
                "channel": 1,
                "datamode": Buffer.DATAMODE.DATAMODE_FFT,
                "bit_resolution": 2,
                "compression_time": 4,
                "compression_frq": 4,
            },
        ),
    ],
)
def test_buffer_to_metadata(filepath, data):
    mock_buffer = MockBuffer(filepath, **data)
    metadata = BM.buffer_to_metadata(mock_buffer)
    assert metadata.directory_path == mock_buffer.directory_path  # type: ignore
    assert metadata.filename == mock_buffer.filename  # type: ignore
    assert metadata.header_hash == mock_buffer.header_hash  # type: ignore
    assert metadata.process == mock_buffer.process  # type: ignore
    assert metadata.channel == mock_buffer.channel  # type: ignore
    assert metadata.datamode == mock_buffer.datamode  # type: ignore


def test_add_files_to_cache(cache):
    # test different batch sizes
    # test different file names

    pass


def test_get_non_synchronized_files():
    pass


def test_synchronize_directory():
    # test whether files from a tempdir are correctly inserted
    # test glob and rglob
    # test the glob and regex patterns
    # check that invalid files are ignored
    pass


def test_remove_files_from_cache():
    pass


def test_get_buffer_metadata():
    # the rest of the functionality should work
    pass


def test_get_buffer_metadata_query():
    # test for equal results
    pass
