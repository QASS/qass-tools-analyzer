from deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil
import pytest
import mock


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
    real_length = len(os.listdir(tmp_data_directory))
   
    # delete tmp_directory
    delete_directory(tmp_data_directory)
    
    # Assert
    assert  real_length == expected_length

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
    
    real_length = len(os.listdir(tmp_data_directory))
   
    # delete tmp_directory
    delete_directory(tmp_data_directory)
    
    # Assert
    assert  real_length == expected_length

# mocked version
@pytest.fixture
def deletehandler_obj_helper():
    current_path = Path(__file__).parent.resolve()
    pattern = "*.txt"

    obj = DeleteHandler(current_path, pattern)
    return obj

def test_delete_by_amount_two(mocker, monkeypatch, obj_deleter):
    # Arrange
    amount_limit = 1
    amount = 3

    def get_oldest_wrapper(some_list):
        return some_list

    monkeypatch.setenv("dir_amount", amount)
    monkeypatch.setattr(DeleteHandler, "__get_oldest", get_oldest_wrapper)
    mock_deleting = mocker.patch("deleting_process.DeleteHandler.__delete_files", return_value=None)
    
    # Act
    obj_deleter.delete_by_amount(amount_limit)
    
    # Assert
    assert mock_deleting.assert_called()
