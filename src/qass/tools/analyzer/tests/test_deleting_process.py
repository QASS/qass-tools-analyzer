#
# Copyright (c) 2022 QASS GmbH.
# Website: https://qass.net
# Contact: QASS GmbH <info@qass.net>
#
# This file is part of Qass tools 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import glob
from  qass.tools.analyzer.deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil
import pytest
from unittest.mock import Mock

# mocked version
@pytest.fixture
def deletehandler_obj_helper(tmp_path):
    pattern = "*.txt"
    obj = DeleteHandler(tmp_path, pattern)
    return obj

@pytest.fixture
def deletehandler_obj_helper_two(tmp_path):
    pattern = "*.txt"
    obj = DeleteHandler(tmp_path, pattern, log_entries=True)
    return obj

@pytest.fixture
def get_oldest_helper(monkeypatch):
    def get_oldest_wrapper(self, some_list):
        test_list = [('Tue Jul  5 11:47:07 2022', '/home/opti/tmp_dir/Text File.txt'), ('Tue Jul  5 11:47:14 2022', '/home/opti/tmp_dir/Text File (1).txt'), ('Tue Jun 14 16:49:34 2022', '/home/opti/tmp_dir/file1.txt')]
        return test_list
    
    monkeypatch.setattr(DeleteHandler, "_DeleteHandler__get_oldest", get_oldest_wrapper)

def test_delete_by_amount(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
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

def test_delete_by_disk_space(monkeypatch, deletehandler_obj_helper, get_oldest_helper):
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

def test_delete_by_amount_two(monkeypatch, deletehandler_obj_helper_two, tmp_path, get_oldest_helper):
    # Arrange
    amount_limit = 1
    os_mock = Mock()
    len_mock = Mock(return_value=[0,1,2])
    monkeypatch.setattr(glob, "glob",len_mock)
    monkeypatch.setattr(os, "remove", os_mock)
    expected_path = tmp_path / Path("*.txt" + ".log")
    
    # Act
    deletehandler_obj_helper_two.delete_by_amount(amount_limit)
    
    # Assert
    assert os_mock.call_count == 2
    assert os.path.exists(expected_path)

def test_delete_by_disk_space_two(monkeypatch, deletehandler_obj_helper_two, tmp_path, get_oldest_helper):
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
    expected_path = tmp_path / Path("*.txt" + ".log")
    # Act
    deletehandler_obj_helper_two.delete_by_disk_space(usage_limit)
    
    # Assert
    assert os_mock.call_count == 2
    assert os.path.exists(expected_path)