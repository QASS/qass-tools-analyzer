import pytest
from unittest.mock import MagicMock
from qass.tools.analyzer.buffer_parser import Buffer
import pickle

def test_pickle():
	mock_buffer = Buffer('test/path')
	pickled_mock_buffer = pickle.dumps(mock_buffer)
	unpickled_mock_buffer = pickle.loads(pickled_mock_buffer)
	assert mock_buffer.__dict__ == unpickled_mock_buffer.__dict__
