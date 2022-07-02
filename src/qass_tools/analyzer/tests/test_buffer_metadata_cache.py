import sys, datetime
sys.path.append("../")
from importlib import reload
from analyzer import buffer_metadata_cache as bmc
from sqlalchemy import create_engine, MetaData, create_mock_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
import pytest
reload(bmc)

@pytest.fixture()
def buffer_objects():
	filenames = ("foo.000", "bar.000", "hoo.000")
	buffers = []

	for file in filenames:
		buffers.append(bmc.BufferMetadataCache.BufferMetadata(filepath = "./" + file, filename = file))
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
	assert "hello.000" in cache.get_non_synchronized_files(None, ["foo.000", "hello.000"])
	assert not "foo.000" in cache.get_non_synchronized_files(None, ["foo.000", "hello.000"])
	assert len(cache.get_non_synchronized_files(None, ["foo.000", "bar.000"])) == 0
















