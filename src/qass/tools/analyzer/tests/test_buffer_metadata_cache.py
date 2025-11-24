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

from qass.tools.analyzer.buffer_metadata_cache import (
    BufferMetadataCache as BMC,
    BufferMetadata as BM,
)
from qass.tools.analyzer.buffer_parser import Buffer
from qass.tools.analyzer.testing import MockBuffer
from sqlalchemy import inspect, func, select
import pytest

SEED = 42


@pytest.fixture(scope="function")
def cache():
    """Returns a BufferMetadataCache instance with an in memory database"""
    cache = BMC(Buffer_cls=MockBuffer)  # type: ignore
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


@pytest.mark.parametrize(
    "filenames,datas",
    [
        (["foo"], [{"process": 1}]),
        (["foo", "bar", "hoo"], [{}, {}, {}]),
        (["foo", "bar", "foo"], [{}, {}, {}]),
        (
            ["foo", "bar", "hoo"],
            [
                {"process": 2, "compression_time": 1},
                {"header_hash": str(uuid4())},
                {"compression_time": 4, "compression_frq": 8},
            ],
        ),
    ],
)
def test_add_files_to_cache(tmp_path, cache, filenames, datas):
    files = [tmp_path / filename for filename in filenames]
    unique_files = set(files)
    for file, data in zip(files, datas):
        if file.exists():
            # skip duplicate files
            continue
        with open(file, "w") as f:
            json.dump(data, f)
    cache.add_files_to_cache(files)
    with cache.Session() as session:
        for filename, data in zip(filenames, datas):
            bm = session.query(BM).filter(BM.filename == filename).first()
            assert bm is not None, f"File {filename} is missing from the cache"
            for key, value in data.items():
                assert getattr(bm, key) == value, (
                    f"key: {key} did not match: {getattr(bm, key), value}"
                )
        assert session.query(func.count(BM.id)).scalar() == len(unique_files)


def test_add_files_to_cache_no_check_synced(tmp_path, cache):
    file = tmp_path / "a"
    with open(file, "w") as f:
        json.dump({"header_hash": file.name}, f)
    cache.add_files_to_cache([file] * 10, check_synced=False)
    with cache.Session() as session:
        assert session.query(func.count(BM.id)).scalar() == 10


def test_add_files_to_cache_invalid_file(tmp_path, cache):
    # Invalid files should be ignored silently
    file = tmp_path / "invalid.txt"
    with open(file, "w") as f:
        f.write("invalid data")
    cache.add_files_to_cache([file])
    with cache.Session() as session:
        bm = session.query(BM).first()
        assert bm is None


@pytest.mark.parametrize(
    "synced, new_hashes, machine_id, r_unsynced, r_stale",
    [
        ([BM(filename="0", header_hash="0")], ["0"], None, [], []),
        (
            [BM(filename="0", header_hash="0"), BM(filename="1", header_hash="1")],
            ["0"],
            None,
            [],
            ["1"],
        ),
        (
            [BM(filename="0", header_hash="0"), BM(filename="1", header_hash="1")],
            ["0", "2", "3"],
            None,
            ["2", "3"],
            ["1"],
        ),
        (
            [],
            ["0", "2", "3"],
            None,
            ["0", "2", "3"],
            [],
        ),
        (
            [
                BM(filename="0", header_hash="0", machine_id="0.0.0.0"),
                BM(filename="1", header_hash="1"),
            ],
            ["0", "1", "2", "3"],
            "0.0.0.0",
            ["1", "2", "3"],
            [],
        ),
        (
            [BM(filename=str(i), header_hash=str(i)) for i in range(200)],
            [str(i) for i in range(100)],
            None,
            [],
            [str(i) for i in range(100, 200)],
        ),
    ],
)
def test_get_non_synchronized_files(
    tmp_path, cache, synced, new_hashes, machine_id, r_unsynced, r_stale
):
    with cache.Session() as session:
        for bm in synced:
            bm.directory_path = str(tmp_path.resolve())
            session.add(bm)
        session.commit()

    new_files = []
    for hash_ in new_hashes:
        # name files same as their hashes
        test_file = tmp_path / hash_
        with open(test_file, "w") as f:
            json.dump({"header_hash": hash_}, f)
        new_files.append(test_file)
    unsynced, stale = cache.get_non_synchronized_files(new_files, machine_id=machine_id)
    unsynced_files = [tmp_path / hash_ for hash_ in r_unsynced]
    stale_files = [tmp_path / hash_ for hash_ in r_stale]
    assert len(set(unsynced).difference(set(unsynced_files))) == 0
    assert len(set(stale).difference(set(stale_files))) == 0


def test_get_non_synchronized_files_invalid_files(tmp_path, cache):
    file = tmp_path / "invalid.txt"
    with open(file, "w") as f:
        f.write("invalid data")
    _, _ = cache.get_non_synchronized_files([file])
    assert True


def test_synchronize_directory(tmp_path, cache):
    N = 100
    files = [tmp_path / str(i) for i in range(N)]
    for file in files:
        with open(file, "w") as f:
            json.dump({"header_hash": file.stem}, f)
    cache.synchronize_directory(tmp_path, glob_pattern="*", regex_pattern=".*")
    with cache.Session() as session:
        synced_files = session.query(func.count(BM.id)).scalar()
    assert synced_files == N


def test_remove_files_from_cache(tmp_path, cache):
    synced = [
        BM(filename="0", directory_path="./", header_hash="0"),
        BM(filename="1", directory_path="./", header_hash="1"),
        BM(filename="2", directory_path="./", header_hash="2"),
    ]
    with cache.Session() as session:
        for bm in synced:
            session.add(bm)
        session.commit()
        assert session.query(func.count(BM.id)).scalar() == 3
    test_file = tmp_path / "1"
    with open(test_file, "w") as f:
        json.dump({"header_hash": "1"}, f)
    cache.remove_files_from_cache([test_file])
    with cache.Session() as session:
        assert session.query(func.count(BM.id)).scalar() == 2
        synced_bm = session.query(BM).all()
        for bm in synced_bm:
            assert bm.header_hash in ("0", "2")


def test_get_matching_metadata(cache):
    synced = [
        BM(filename="0", directory_path="./", header_hash="0", process=1),
        BM(filename="1", directory_path="./", header_hash="1", process=2),
        BM(filename="2", directory_path="./", header_hash="2", process=3),
    ]
    with cache.Session() as session:
        for bm in synced:
            session.add(bm)
        session.commit()
        assert session.query(func.count(BM.id)).scalar() == 3
        results = cache.get_matching_metadata(select(BM).filter(BM.process < 3))
        assert len(results) == 2


def test_get_matching_buffers(tmp_path, cache):
    data = [
        {"header_hash": "0", "process": 0},
        {"header_hash": "1", "process": 1},
        {"header_hash": "2", "process": 2},
        {"header_hash": "3", "process": 3},
    ]
    for d in data:
        file = tmp_path / d["header_hash"]
        with file.open(mode="w") as f:
            json.dump(d, f)
    cache.synchronize_directory(tmp_path, glob_pattern="*", regex_pattern=".*")
    buffers = cache.get_matching_buffers(select(BM))
    assert len(buffers) == 4


def test_get_buffer_metadata_query(cache):
    synced = [
        BM(filename="0", directory_path="./", header_hash="0", process=1),
        BM(filename="1", directory_path="./", header_hash="1", process=2),
        BM(filename="2", directory_path="./", header_hash="2", process=3),
    ]
    with cache.Session() as session:
        for bm in synced:
            session.add(bm)
        session.commit()
    match_result = cache.get_matching_metadata(select(BM).filter(BM.process == 2))
    query_result = cache.get_matching_metadata(
        cache.get_buffer_metadata_query(BM(process=2))
    )
    match_hashes = set(map(lambda bm: bm.header_hash, match_result))
    query_hashes = set(map(lambda bm: bm.header_hash, query_result))
    assert len(match_hashes.difference(query_hashes)) == 0
