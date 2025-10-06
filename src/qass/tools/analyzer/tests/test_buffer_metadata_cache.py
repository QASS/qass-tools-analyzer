# ruff: noqa
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
import sys, datetime
from uuid import uuid4
from enum import Enum


sys.path.append("../")
sys.path.append("../../")
from importlib import reload
from qass.tools.analyzer import buffer_metadata_cache as bmc
from qass.tools.analyzer.buffer_parser import Buffer
from sqlalchemy import select, inspect
import pytest

reload(bmc)


@pytest.fixture
def mock_buffer():
    class Mock_Buffer:
        def __init__(self, filepath, *args):
            self.filepath = filepath

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        @property
        def process(self):
            return 1

        @property
        def channel(self):
            return 1

        @property
        def foo(self):
            return "foo"

    return Mock_Buffer


@pytest.fixture()
def buffer_objects():
    filenames = ("foop1c0b.000", "barp1c0b.000", "hoop1c0b.000")
    buffers = []

    for file in filenames:
        buffers.append(
            bmc.BufferMetadataCache.BufferMetadata(directory_path="./", filename=file)
        )
    return buffers


@pytest.fixture(scope="function")
def cache():
    cache = bmc.BufferMetadataCache(Buffer)
    return cache


def test_session_creation():
    cache = bmc.BufferMetadataCache()
    inspector = inspect(cache.engine)
    assert "buffer_metadata" in inspector.get_table_names()


@pytest.mark.parametrize(
    "pre_added_files,new_files,unsynced_files,missing_files",
    [
        (
            [],
            ["./foop1c0b0.000", "./hellop1c0b0.000"],
            ["./foop1c0b0.000", "./hellop1c0b0.000"],
            [],
        ),
        (
            ["./hoop1c0b0.000"],
            ["./foop1c0b0.000", "./hellop1c0b0.000"],
            ["./foop1c0b0.000", "./hellop1c0b0.000"],
            ["./hoop1c0b0.000"],
        ),
    ],
)
def test_get_non_synchronized_files(
    cache, pre_added_files, new_files, unsynced_files, missing_files
):
    with cache.Session() as session:
        for pre_added_file in pre_added_files:
            _, file = pre_added_file.split("/")
            session.add(
                bmc.BufferMetadataCache.BufferMetadata(
                    directory_path="./", filename=file
                )
            )
            session.commit()
    unsynchronized_files, synced_but_missing_files = cache.get_non_synchronized_files(
        new_files, None
    )
    for unsynced_file in unsynced_files:
        assert unsynced_file in unsynchronized_files
    for pre_added_file in pre_added_files:
        assert not pre_added_file in unsynchronized_files
    for missing_file in missing_files:
        assert missing_file in synced_but_missing_files


def test_get_non_synchronized_files_more_files(cache):
    N = 1000
    path = "/home/"
    files = [path + str(i) for i in range(N)]
    unsynchronized_files, _ = cache.get_non_synchronized_files(files, None)
    assert len(unsynchronized_files) == len(files)


def test_get_non_synchronized_files_more_files_duplicates(cache):
    N = 1000
    DUPLICATES = 100
    path = "/home/"
    files = [str(uuid4()) for _ in range(N)]
    with cache.Session() as session:
        for _ in range(DUPLICATES):
            filename = str(uuid4())
            file = path + filename
            session.add(
                bmc.BufferMetadataCache.BufferMetadata(
                    directory_path=path, filename=filename
                )
            )
            files.append(file)
        session.commit()
    unsynchronized_files, _ = cache.get_non_synchronized_files(files, None)
    assert len(unsynchronized_files) == N


def test_buffer_to_buffer_metadata(mock_buffer):
    buffer_metadata = bmc.BufferMetadata.buffer_to_metadata(
        mock_buffer("./foop1c0b.000")
    )
    assert buffer_metadata.directory_path == "./"
    assert buffer_metadata.filename == "foop1c0b.000"
    assert buffer_metadata.process == 1
    assert buffer_metadata.channel == 1
    with pytest.raises(AttributeError) as e:  # invalid props shouldn't be copied
        getattr(buffer_metadata, "foo")


def test_buffer_to_buffer_metadata_different_filepath():
    class Mock_Buffer:
        @property
        def filepath(self):
            return ".\\foop1c0b.000"

        @property
        def process(self):
            return 1

        @property
        def channel(self):
            return 1

        @property
        def foo(self):
            return "foo"

    buffer_metadata = bmc.BufferMetadata.buffer_to_metadata(Mock_Buffer())
    assert buffer_metadata.directory_path == ".\\"


def test_get_matching_files_single_property(cache, mock_buffer):
    with cache.Session() as session:
        cache.Buffer_cls = mock_buffer
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./", filename="foop1c0b.000", process=1
            )
        )
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./", filename="hoop1c0b.000", process=2
            )
        )
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./", filename="barp1c0b.000", process=1
            )
        )
        session.commit()
    query = select(bmc.BufferMetadata).filter(bmc.BufferMetadata.process == 1)
    assert "./foop1c0b.000" in cache.get_matching_files(query)
    assert "./barp1c0b.000" in cache.get_matching_files(query)
    assert not "./hoop1c0b.000" in cache.get_matching_files(query)


def test_get_matching_files_multiple_properties(cache, mock_buffer):
    with cache.Session() as session:
        cache.Buffer_cls = mock_buffer
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./", filename="foop1c0b.000", process=1, frq_bands=16
            )
        )
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./",
                filename="hoop1c0b.000",
                process=2,
                channel=2,
                frq_bands=512,
            )
        )
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./",
                filename="barp1c0b.000",
                process=1,
                channel=1,
                frq_bands=16,
            )
        )
        session.add(
            bmc.BufferMetadataCache.BufferMetadata(
                directory_path="./",
                filename="foo_barp1c0b.000",
                process=1,
                channel=2,
                frq_bands=512,
            )
        )
        session.commit()
    query = select(bmc.BufferMetadata).filter(bmc.BufferMetadata.process == 1)
    assert "./foop1c0b.000" in cache.get_matching_files(query)
    assert not "./hoop1c0b.000" in cache.get_matching_files(query)
    assert "./barp1c0b.000" in cache.get_matching_files(query)
    assert "./foo_barp1c0b.000" in cache.get_matching_files(query)
    query = select(bmc.BufferMetadata).filter(
        bmc.BufferMetadata.process == 1, bmc.BufferMetadata.channel == 1
    )
    assert not "./foop1c0b.000" in cache.get_matching_files(query)
    assert not "./hoop1c0b.000" in cache.get_matching_files(query)
    assert "./barp1c0b.000" in cache.get_matching_files(query)
    assert not "./foo_barp1c0b.000" in cache.get_matching_files(query)
    query = select(bmc.BufferMetadata).filter(
        bmc.BufferMetadata.frq_bands == 16, bmc.BufferMetadata.channel == 1
    )
    assert not "./foop1c0b.000" in cache.get_matching_files(query)
    assert not "./hoop1c0b.000" in cache.get_matching_files(query)
    assert "./barp1c0b.000" in cache.get_matching_files(query)
    assert not "./foo_barp1c0b.000" in cache.get_matching_files(query)


def test_buffermetadata_constructor():
    class TestEnum(Enum):
        TEST = 0

    buffer_metadata = bmc.BufferMetadata(datakind=TestEnum.TEST)
    assert buffer_metadata.datakind == TestEnum.TEST


def test_get_matching_files_enum_properties(cache, mock_buffer):
    with cache.Session() as session:
        cache.Buffer_cls = mock_buffer
        session.add(
            bmc.BufferMetadata(
                directory_path="./",
                filename="foop1c0b.000",
                process=1,
                datatype=Buffer.DATATYPE.COMP_MOV_AVERAGE,
            )
        )
        session.add(
            bmc.BufferMetadata(
                directory_path="./",
                filename="hoop1c0b.000",
                process=2,
                datatype=Buffer.DATATYPE.COMP_MOV_AVERAGE,
            )
        )
        session.add(
            bmc.BufferMetadata(
                directory_path="./",
                filename="barp1c0b.000",
                process=1,
                datatype=Buffer.DATATYPE.COMP_MOV_AVERAGE_FRQ,
            )
        )
        session.commit()
    query = select(bmc.BufferMetadata).filter(
        bmc.BufferMetadata.process == 1,
        bmc.BufferMetadata.datatype == Buffer.DATATYPE.COMP_MOV_AVERAGE,
    )
    assert "./foop1c0b.000" in cache.get_matching_files(query)


@pytest.mark.parametrize(
    "filepath,directory_path,filename",
    [
        ("./foo/bar/hoo", "./foo/bar/", "hoo"),
        ("\\hello\\file\\filename", "\\hello\\file\\", "filename"),
        ("./foop1c0b.000", "./", "foop1c0b.000"),
        ("./foop1c0b01.000", "./", "foop1c0b01.000"),
    ],
)
def test_split_filepath(filepath, directory_path, filename):
    path, f_name = bmc.BufferMetadataCache.split_filepath(filepath)
    assert path == directory_path
    assert f_name == filename
