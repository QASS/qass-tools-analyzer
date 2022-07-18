import sys, datetime
from uuid import uuid4
from enum import Enum


sys.path.append("../")
sys.path.append("../../")
from importlib import reload
from analyzer import buffer_metadata_cache as bmc
from analyzer.buffer_parser import Buffer
from sqlalchemy import create_engine, MetaData, create_mock_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
import pytest
reload(bmc)

@pytest.fixture
def mock_buffer():
    class Mock_Buffer:
        def __init__(self, *args): pass
        def __enter__(self):
            return self
        def __exit__(self, *args): pass
        @property
        def filepath(self): return "./foop1c0b.000"
        @property
        def process(self): return 1
        @property
        def channel(self): return 1
        @property
        def foo(self): return "foo"
    return Mock_Buffer

@pytest.fixture()
def buffer_objects():
    filenames = ("foop1c0b.000", "barp1c0b.000", "hoop1c0b.000")
    buffers = []

    for file in filenames:
        buffers.append(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = file))
    return buffers

@pytest.fixture(scope="session")
def db_url():
    yield "sqlite:///buffer_metadata_db"

@pytest.fixture(scope='session')
def db_engine(db_url):
    """yields a SQLAlchemy engine which is suppressed after the test session"""
    #db_url = request.config.getoption("--dburl")
    engine_ = create_engine(db_url, echo=True)

    yield engine_

    engine_.dispose()

@pytest.fixture(scope='session')
def db_session_factory(db_engine):
    """returns a SQLAlchemy scoped session factory"""
    return scoped_session(sessionmaker(bind=db_engine))


@pytest.fixture(scope='function')
def db_session(db_session_factory):
    """yields a SQLAlchemy connection which is rollbacked after the test"""
    session_ = db_session_factory()

    yield session_

    session_.rollback()
    session_.close()

def test_session_creation():
    session = bmc.BufferMetadataCache.create_session()
    engine = session.get_bind()
    inspector = inspect(engine)
    assert "buffer_metadata" in inspector.get_table_names()

def test_get_non_synchronized_files(db_session, buffer_objects):
    db_session.add_all(buffer_objects)
    cache = bmc.BufferMetadataCache(db_session)
    assert "./hellop1c0b.000" in cache.get_non_synchronized_files(["./foop1c0b.000", "./hellop1c0b.000"])
    assert not "./foop1c0b.000" in cache.get_non_synchronized_files(["./foop1c0b.000", "./hellop1c0b.000"])
    assert len(cache.get_non_synchronized_files(["./foop1c0b.000", "./barp1c0b.000"])) == 0

def test_get_non_synchronized_files_more_files(db_session):
    N = 1000
    path = "/home/"
    files = [path + str(uuid4()) for _ in range(N)]
    cache = bmc.BufferMetadataCache(db_session)
    assert len(cache.get_non_synchronized_files(files)) == N

def test_get_non_synchronized_files_more_files_duplicates(db_session):
    N = 1000
    DUPLICATES = 100
    path = "/home/"
    files = [str(uuid4()) for _ in range(N)]
    for _ in range(100):
        filename = str(uuid4())
        file = path + filename
        db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = path, filename = filename))
        files.append(file)
    cache = bmc.BufferMetadataCache(db_session)
    assert len(cache.get_non_synchronized_files(files)) == N

def test_buffer_to_buffer_metadata(mock_buffer):
    buffer_metadata = bmc.BufferMetadata.buffer_to_metadata(mock_buffer())
    assert buffer_metadata.directory_path == "./"
    assert buffer_metadata.filename == "foop1c0b.000"
    assert buffer_metadata.process == 1
    assert buffer_metadata.channel == 1
    with pytest.raises(AttributeError) as e: # invalid props shouldn't be copied
        getattr(buffer_metadata, "foo")

def test_buffer_to_buffer_metadata_different_filepath():
    class Mock_Buffer:
        @property
        def filepath(self): return ".\\foop1c0b.000"
        @property
        def process(self): return 1
        @property
        def channel(self): return 1
        @property
        def foo(self): return "foo"
    
    buffer_metadata = bmc.BufferMetadata.buffer_to_metadata(Mock_Buffer())
    assert buffer_metadata.directory_path == ".\\"


def test_add_files_to_cache(db_session, mock_buffer, mocker):
    
    bm_cache = bmc.BufferMetadataCache(db_session, mock_buffer)
    mocker.patch.object(bm_cache._db, "commit") # ensure the database session doesn't commit
    bm_cache.add_files_to_cache(["./foop1c0b.000"])
    buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).first()
    assert buffer_metadata.filename == "foop1c0b.000"
    bm_cache._db.commit.assert_called_once()

def test_add_files_to_cache_warning(db_session, mocker):
    class Buffer:
        def __init__(self, *args): 
            raise ValueError("Test Error")
    bm_cache = bmc.BufferMetadataCache(db_session, Buffer)
    mocker.patch.object(bm_cache._db, "commit") # ensure the database session doesn't commit
    with pytest.warns(UserWarning):
        bm_cache.add_files_to_cache(["./foop1c0b.000"])
    buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).first()
    assert buffer_metadata.filename == "foop1c0b.000"
    bm_cache._db.commit.assert_called_once()

def test_synchronize_directory(db_session, mock_buffer, mocker):

    cache = bmc.BufferMetadataCache(db_session, mock_buffer) # it's important that the filename property of mock_bfufer returns "foo.000"
    mocker.patch("analyzer.buffer_metadata_cache.Path.glob", return_value = ["./foop1c0b.000"])    
    mocker.patch("os.path.isfile", return_value = True)
    mocker.patch.object(cache._db, "commit") # ensure the database session doesn't commit
    cache.synchronize_directory("./", sync_subdirectories = False)
    db_session.query(bmc.BufferMetadataCache.BufferMetadata).all()
    buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).one()
    assert buffer_metadata.filename == "foop1c0b.000"

    # mocker.patch("analyzer.buffer_metadata_cache.Path.rglob", return_value = ["./barp1c0b.000"])
    # cache.synchronize_directory("./", recursive = True)
    # # db_session.query(bmc.BufferMetadataCache.BufferMetadata).all()
    # buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).first()
    # print("METADATA", buffer_metadata.filename)
    # assert buffer_metadata.filename == "barp1c0b.000"


def test_get_matching_files_single_property(db_session, mock_buffer):
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "foop1c0b.000", process = 1))
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "hoop1c0b.000", process = 2))
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "barp1c0b.000", process = 1))
    cache = bmc.BufferMetadataCache(db_session, mock_buffer)
    db_session.query(bmc.BufferMetadataCache.BufferMetadata).all() # this is needed in order for the session to have the objects ready
    metadata = bmc.BufferMetadataCache.BufferMetadata(process = 1)
    assert "./foop1c0b.000" in cache.get_matching_files(metadata)
    assert "./barp1c0b.000" in cache.get_matching_files(metadata)
    assert not "./hoop1c0b.000" in cache.get_matching_files(metadata)
    
def test_get_matching_files_multiple_properties(db_session, mock_buffer):
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "foop1c0b.000", process = 1, frq_bands = 16))
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "hoop1c0b.000", process = 2, channel = 2, frq_bands = 512))
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "barp1c0b.000", process = 1, channel = 1, frq_bands = 16))
    db_session.add(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./", filename = "foo_barp1c0b.000", process = 1, channel = 2, frq_bands = 512))
    cache = bmc.BufferMetadataCache(db_session, mock_buffer)
    db_session.query(bmc.BufferMetadataCache.BufferMetadata).all()
    metadata = bmc.BufferMetadataCache.BufferMetadata(process = 1)
    assert "./foop1c0b.000" in cache.get_matching_files(metadata)
    assert not "./hoop1c0b.000" in cache.get_matching_files(metadata)
    assert "./barp1c0b.000" in cache.get_matching_files(metadata)
    assert "./foo_barp1c0b.000" in cache.get_matching_files(metadata)
    metadata = bmc.BufferMetadataCache.BufferMetadata(process = 1, channel = 2)
    assert not "./foop1c0b.000" in cache.get_matching_files(metadata)
    assert not "./hoop1c0b.000" in cache.get_matching_files(metadata)
    assert not "./barp1c0b.000" in cache.get_matching_files(metadata)
    assert "./foo_barp1c0b.000" in cache.get_matching_files(metadata)
    metadata = bmc.BufferMetadataCache.BufferMetadata(frq_bands = 16, channel = 1)
    assert not "./foop1c0b.000" in cache.get_matching_files(metadata)
    assert not "./hoop1c0b.000" in cache.get_matching_files(metadata)
    assert "./barp1c0b.000" in cache.get_matching_files(metadata)
    assert not "./foo_barp1c0b.000" in cache.get_matching_files(metadata)

def test_buffermetadata_constructor():
    class TestEnum(Enum):
        TEST = 0
    buffer_metadata = bmc.BufferMetadata(datakind = TestEnum.TEST)
    assert buffer_metadata.datakind == TestEnum.TEST


def test_get_matching_files_enum_properties(db_session, mock_buffer):
    db_session.add(bmc.BufferMetadata(directory_path = "./", filename = "foop1c0b.000", process = 1, datatype = Buffer.DATATYPE.COMP_MOV_AVERAGE))
    db_session.add(bmc.BufferMetadata(directory_path = "./", filename = "hoop1c0b.000", process = 2, datatype = Buffer.DATATYPE.COMP_MOV_AVERAGE))
    db_session.add(bmc.BufferMetadata(directory_path = "./", filename = "barp1c0b.000", process = 1, datatype = Buffer.DATATYPE.COMP_MOV_AVERAGE_FRQ))
    cache = bmc.BufferMetadataCache(db_session, mock_buffer)
    db_session.query(bmc.BufferMetadataCache.BufferMetadata).all()
    metadata = bmc.BufferMetadataCache.BufferMetadata(process = 1, datatype = Buffer.DATATYPE.COMP_MOV_AVERAGE)
    assert "./foop1c0b.000" in cache.get_matching_files(filter_function=lambda bm: bm.process == 1 and bm.datatype == Buffer.DATAKIND.COMP_MOV_AVERAGE)
    assert "./foop1c0b.000" in cache.get_matching_files(metadata)

@pytest.mark.parametrize("filepath,directory_path,filename", [("./foo/bar/hoo", "./foo/bar/", "hoo"), ("\\hello\\file\\filename", "\\hello\\file\\", "filename")])
def test_split_filepath(filepath, directory_path, filename):
    path, f_name = bmc.BufferMetadataCache.split_filepath(filepath)
    assert path == directory_path
    assert f_name == filename