import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine, MetaData, create_mock_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from analyzer.buffer_parser import BufferErrorLogger


@pytest.fixture(scope="session")
def db_url():
    yield "sqlite:///buffer_error_db"


@pytest.fixture(scope='function')
def db_session(db_url):
    """yields a SQLAlchemy connection which is rollbacked after the test"""
    session_ = BufferErrorLogger.create_session(db_url = db_url)

    yield session_

    session_.rollback()
    session_.close()

@pytest.mark.parametrize("result", (1, "foo", [1, 2, 3]))
def test_buffer_no_error(db_session, result):
	class MockBuffer:
		def __init__(self, *args):
			pass

		def __enter__(self):
			return self

		def __exit__(self, *args):
			pass

		def test(self):
			return result

	bel = BufferErrorLogger(db_session, MagicMock()) # mock the logger
	r = bel.log_errors(MockBuffer, "test", lambda buff: buff.test())
	assert r == result

def test_buffer_error(db_session):
	class MockBuffer:
		def __init__(self, *args):
			pass

		def __enter__(self):
			return self

		def __exit__(self, *args):
			pass

		def test(self):
			raise Exception("TESTING PLEASE IGNORE")

	bel = BufferErrorLogger(db_session, MagicMock()) # mock the logger
	r = bel.log_errors(MockBuffer, "test", lambda buff: buff.test())
	assert r == None
	buffer_error = db_session.query(BufferErrorLogger.BufferError).get("test")
	assert buffer_error is not None
	assert buffer_error.error_type == "<class 'Exception'>"
	assert buffer_error.error_msg == "TESTING PLEASE IGNORE"
	assert buffer_error.function_name == "test"
	assert buffer_error.line_content == "raise Exception(\"TESTING PLEASE IGNORE\")"