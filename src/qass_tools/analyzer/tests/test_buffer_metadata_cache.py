import sys, datetime

sys.path.append("../")
sys.path.append("../../")
from importlib import reload
from analyzer import buffer_metadata_cache as bmc
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
		def filepath(self): return "./foo.000"
		@property
		def process(self): return 1
		@property
		def channel(self): return 1
		@property
		def foo(self): return "foo"
	return Mock_Buffer

@pytest.fixture()
def buffer_objects():
	filenames = ("foo.000", "bar.000", "hoo.000")
	buffers = []

	for file in filenames:
		buffers.append(bmc.BufferMetadataCache.BufferMetadata(directory_path = "./" + file, filename = file))
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
	assert "hello.000" in cache.get_non_synchronized_files("./", ["foo.000", "hello.000"])
	assert not "foo.000" in cache.get_non_synchronized_files("./", ["foo.000", "hello.000"])
	assert len(cache.get_non_synchronized_files(None, ["foo.000", "bar.000"])) == 0

def test_buffer_to_buffer_metadata(mock_buffer):
	buffer_metadata = bmc.BufferMetadataCache.buffer_to_metadata(mock_buffer())
	assert buffer_metadata.directory_path == "./"
	assert buffer_metadata.filename == "foo.000"
	assert buffer_metadata.process == 1
	assert buffer_metadata.channel == 1
	with pytest.raises(AttributeError) as e: # invalid props shouldn't be copied
		getattr(buffer_metadata, "foo")

def test_buffer_to_buffer_metadata_different_filepath():
	class Mock_Buffer:
		@property
		def filepath(self): return ".\\foo.000"
		@property
		def process(self): return 1
		@property
		def channel(self): return 1
		@property
		def foo(self): return "foo"
	
	buffer_metadata = bmc.BufferMetadataCache.buffer_to_metadata(Mock_Buffer())
	assert buffer_metadata.directory_path == ".\\"


def test_add_files_to_cache(db_session, mock_buffer, mocker):
	
	bm_cache = bmc.BufferMetadataCache(db_session, mock_buffer)
	mocker.patch.object(bm_cache._db, "commit") # ensure the database session doesn't commit
	bm_cache.add_files_to_cache("./", ["foo.000"])
	buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).first()
	assert buffer_metadata.filename == "foo.000"
	bm_cache._db.commit.assert_called_once()

def test_synchronize_directory(db_session, mock_buffer, mocker):

	cache = bmc.BufferMetadataCache(db_session, mock_buffer) # it's important that the filename property of mock_bfufer returns "foo.000"
	mocker.patch("os.listdir", return_value = ["foo.000"])
	mocker.patch("os.path.isfile", return_value = True)
	mocker.patch("os.path.join", return_value = "./foo.000")
	mocker.patch.object(cache._db, "commit") # ensure the database session doesn't commit
	cache.synchronize_directory("./", sync_subdirectories = False)
	buffer_metadata = db_session.query(bmc.BufferMetadataCache.BufferMetadata).one()
	assert buffer_metadata.filename == "foo.000"






