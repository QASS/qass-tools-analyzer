from deleting_process import DeleteHandler
from pathlib import Path
import os
import shutil

def test_delete_by_amount():
    current_path = Path(__file__).parent.resolve()
    tmp_data_directory = current_path / "tmp_dir"
    
    if not os.path.exists(tmp_data_directory):
        tmp_data_directory.mkdir()

    tmp_file = tmp_data_directory / "file1.txt"
    tmp_file.touch()
    tmp_file2 = tmp_data_directory / "file2.txt"
    tmp_file2.touch()
    tmp_file3 = tmp_data_directory / "file3.txt"
    tmp_file3.touch()
    
    pattern = "*.txt"
    
    deleter = DeleteHandler(tmp_data_directory, pattern)
    deleter.delete_by_amount(1)
    assert len(os.listdir(tmp_data_directory)) == 1

    if tmp_data_directory.exists():
        shutil.rmtree(tmp_data_directory)

# mocked version
#def test_delete_by_amount_two():
