from subprocess import call

from psutil import disk_usage
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
        test_list = [('Tue Jul  5 11:47:07 2022', '/home/opti/tmp_dir/Text File.txt'), ('Tue Jul  5 11:47:14 2022', '/home/opti/tmp_dir/Text File (1).txt'), ('Tue Jun 14 16:49:34 2022', '/home/opti/tmp_dir/file1.txt')]
        return test_list
    
    monkeypatch.setattr(DeleteHandler, "_DeleteHandler__get_oldest", get_oldest_wrapper)

def test_delete_by_amount_two(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
    # Arrange
    amount_limit = 1
    amount = "3"
    
    os_mock = Mock()
    
    monkeypatch.setenv("dir_amount", amount)
    monkeypatch.setattr(os, "remove", os_mock)
    
    # Act
    deletehandler_obj_helper.delete_by_amount(amount_limit)
    
    # Assert
    assert os_mock.call_count == 1

def test_delete_by_disk_space_two(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
    # Arrange
    usage_limit = 0.1

    os_mock = Mock()
    shutil_mock = Mock(return_value=(1000, 950, 50))
    filesize_mock = Mock(return_value=25)
    monkeypatch.setattr(shutil, "disk_usage", shutil_mock)
    monkeypatch.setattr(os, "remove", os_mock)
    monkeypatch.setattr(os.path, "getsize", filesize_mock)
    
    # Act
    deletehandler_obj_helper.delete_by_disk_space(usage_limit)
    
    # Assert
    assert os_mock.call_count == 3
