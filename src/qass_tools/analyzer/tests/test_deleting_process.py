from deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil
import pytest

def create_tmp_dir():
    current_path = Path(__file__).parent.resolve()
    tmp_data_directory = current_path / "tmp_dir"
    
    if not os.path.exists(tmp_data_directory):
        tmp_data_directory.mkdir()
    else:
        tmp_data_directory = current_path / "tmp_dir_tests"
        tmp_data_directory.mkdir()

    return tmp_data_directory
    
def create_files(tmp_path, num):
    for n in range(1, num+1):
        appending = "file" + str(n) + ".txt"
        tmp_file = tmp_path / appending
        tmp_file.touch()
  
def delete_directory(directory_path):
    if directory_path.exists():
        shutil.rmtree(directory_path)

def test_delete_by_amount():
    # Arrange
    pattern = "*.txt"
    expected_length = 1
    amount_limit = 1
    file_amount = 3

    tmp_data_directory = create_tmp_dir()
    create_files(tmp_data_directory, file_amount)

    # Act
    deleter = DeleteHandler(tmp_data_directory, pattern)
    deleter.delete_by_amount(amount_limit)
    
    # Assert
    assert len(os.listdir(tmp_data_directory)) == expected_length

    # delete tmp_directory
    delete_directory(tmp_data_directory)

def test_delete_by_disk_space():
    # Arrange
    pattern = "*.txt"
    expected_length = 0
    space_limit = 0.01
    file_amount = 3

    tmp_data_directory = create_tmp_dir()
    create_files(tmp_data_directory, file_amount)

    # Act
    deleter = DeleteHandler(tmp_data_directory, pattern)
    deleter.delete_by_disk_space(space_limit)
    
    # Assert
    assert len(os.listdir(tmp_data_directory)) == expected_length

    # delete tmp_directory
    delete_directory(tmp_data_directory)

# mocked version
""" 
@pytest.fixture
def mock_env_path(monkeypatch):
    current_path = Path(__file__).parent.resolve()
    tmp_data_directory = current_path / "tmp_dir"
    monkeypatch.setenv("self.path", tmp_data_directory)

@pytest.fixture
def mock_env_pattern(monkeypatch):
    pattern = "*.txt"
    monkeypatch.setenv("self.pattern", pattern)

def test_delete_by_amount_two(monkeypatch, mock_env_path, mock_env_pattern):

    def delete(file_list):
        pass

    limit_amount = 1
    amount = 3
    expected_result = 1

    monkeypatch.setattr(DeleteHandler, "__delete_file", delete)
    monkeypatch.setenv("dir_amount", amount)
    
    # assert expected_result to result 
    assert DeleteHandler.delete_by_amount(limit_amount) == expected_result
"""