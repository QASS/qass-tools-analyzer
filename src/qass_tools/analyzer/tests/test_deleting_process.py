import glob
from subprocess import call

from psutil import disk_usage
from deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil
import pytest
import mock
from unittest.mock import Mock

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
    os_mock = Mock()
    len_mock = Mock(return_value=[0,1,2])
    monkeypatch.setattr(glob, "glob",len_mock)
    monkeypatch.setattr(os, "remove", os_mock)
    
    # Act
    deletehandler_obj_helper.delete_by_amount(amount_limit)
    
    # Assert
    assert os_mock.call_count == 2

def test_delete_by_disk_space_two(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
    # Arrange
    usage_limit = 0.9

    os_mock = Mock()
    shutil_mock = Mock(return_value=(1000, 950, 50))
    filesize_mock = Mock(return_value=25)
    len_mock = Mock(return_value=[0,1,2])
    monkeypatch.setattr(shutil, "disk_usage", shutil_mock)
    monkeypatch.setattr(os, "remove", os_mock)
    monkeypatch.setattr(glob, "glob",len_mock)
    monkeypatch.setattr(os.path, "getsize", filesize_mock)
    
    # Act
    deletehandler_obj_helper.delete_by_disk_space(usage_limit)
    
    # Assert
    assert os_mock.call_count == 2
