from subprocess import call
from deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil
import pytest
import mock
from unittest.mock import Mock

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

@pytest.fixture
def get_oldest_helper(monkeypatch):
    def get_oldest_wrapper(self, some_list):
        test_list = [(2010,"filepath1"),(2011,"filepath2"),(2012,"filepath3")]
        return test_list
    
    monkeypatch.setattr(DeleteHandler, "_DeleteHandler__get_oldest", get_oldest_wrapper)

def test_delete_by_amount_two(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
    # Arrange
    amount_limit = 1
    amount = "3"

    os_mock = Mock()

    #def get_oldest_wrapper(self, some_list):
    #    test_list = [(2010,"filepath1"),(2011,"filepath2"),(2012,"filepath3")]
    #    return test_list
    
    
    monkeypatch.setenv("dir_amount", amount)
    #monkeypatch.setattr(DeleteHandler, "_DeleteHandler__get_oldest", get_oldest_wrapper)
    monkeypatch.setattr(os, "remove", os_mock)

    #mock_deleting = mocker.patch("deleting_process.DeleteHandler._DeleteHandler__delete_file", return_value=None)
    
    
    # Act
    deletehandler_obj_helper.delete_by_amount(amount_limit)
    
    # Assert
    #os_mock.assert_has_calls(calls, any_order=True)
    assert os_mock.call_count == 1

