# import modules
from asyncio.log import logger
import time
import sys
import os
import glob
from typing import List, Union
import shutil
import logging, logging.handlers
from pathlib import Path
__all__ = ["DeleteHandler"]

class DeleteHandler():
    """DeleteHandler Class with different functionalities to delete local files on disk. 
    
    With an instance of this class a specific deleting-pattern and path (for the files) will be associated. The programm always looks for the oldest versions of files which match with the pattern.
    Files will be deletet until the maximum amount of allowed files is reached or enough disk space is free. This class stands for now on its own. With a def main() syntacs it will be executed by programm start.
    
    :param path: Local directory path.
    :type path: str
    :param pattern: Searched pattern.
    :type pattern: str
    :param pattern: Flag if log file should be created (by default: False)
    :type log_entires: bool
    """
    def __init__(self, path: str, pattern: str, log_entries=False) -> None:
        """Constructor to connect a specific local directory path with a specific pattern parsed.

        Provided functions can be applied later for each combination. Pattern has to be according to the rules used by Unix shell (used glob module is based on that). In the following Unix Shell rules are provided:
        | Pattern | Meaning                               | Example                                                                              |
        | ------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
        | *	      | Matches everything	                  | *.pdf matches all files with the pdf extension                                       |
        | ?	      | Matches any single character	      | sales/??.jpeg matches all files with two characters long present in the sales folder |
        | []	  | Matches any character in the sequence |	[psr]* matches all files starting with the letter p, s, or r                         |
        | [!]	  | Matches any character not in sequence |	[!psr]* matches all files not starting with the letter p, s, or r                    |
        
        For a literal match, wrap the meta-characters in brackets. For example, '[?]' matches the character '?'    
        NOTE: Created logfile be ignored automatically.

        :param path: Local directory path.
        :type path: str
        :param pattern: Searched pattern.
        :type pattern: str
        """
        self.path = path
        self.pattern = pattern
        self.log_entries = log_entries
        self.full_path = str(Path(self.path) / Path(self.pattern))
        if self.log_entries:
            #logfilesize_limit = amount of entires * average entry size(=200bytes)
            logfilesize_limit = 10000 * 200
            self.file_logger = self._create_file_logger_obj(self.path, self.pattern, logfilesize_limit)
        
    def delete_by_amount(self, max_amount: int) -> None:
        """Provided function to delete files based on file amount in location if amount overruns defined limit.

        :param max_amount: Maximum amount (limit) of files allowed in this directory which are match pattern.
        :type max_amount: int
        :raises OSError: Exception is raised if deleting process cannot be completed. Either because there are not enough files that match pattern to satisfy limit or because any other wild error appears. 
        """
        # search for files in directory which match pattern
        delete_list = glob.glob(self.full_path) # delete_list is saved with full path
        file_amount = len(delete_list)
        if file_amount <= 0:
            if self.log_entries:
                self.file_logger.warning("The current deleting directory has no matching files to delete. Check your pattern or check if the directory is correct.") 
            return
        # calc how many files have to be deletet in order to satisfy limit
        amount_to_delete = file_amount - max_amount
        
        # if there are any files to delete:
        if amount_to_delete > 0:
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            for idx in range(0, amount_to_delete):
                self.__delete_file(sorted_list[idx][1])
            
        
    def delete_by_disk_space(self, disk_usage_limit: float) -> None:
        """Provided method to delete files by a given maximum disk space usage.

        :param disk_usage_limit: Limit how much disk memory is allowed to use at maximum. Parsed as part of the whole.
        :type disk_usage_limit: float
        :raises OSError: Exception is raised if deleting process cannot be compelted. Either because there are not enough files that match pattern to satisfy limit or because any other wild error appears. 
        """
        # read out currently used disk usage
        disk_usage = shutil.disk_usage(self.path)
        # help to debug: disk_usage[0] = total // disk_usage[1] = used // disk_usage[2] = free
        # calc free space that is required based on user limit
        target_free_space = disk_usage[0] * (1 - disk_usage_limit)
        # calc therefore required space
        space_to_make = abs(target_free_space - disk_usage[2])
        
        if space_to_make > 0:
            delete_list = glob.glob(self.full_path) # delete_list is saved with full path
            if len(delete_list) == 0:
                if self.log_entries:
                   self.file_logger.warning("The current deleting directory has no matching files to delete. Check your pattern or check if the directory is correct.") 
                return
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            # helper
            filesize = 0
            #n = -1
            for n, (date, file) in enumerate(sorted_list):
                filesize = filesize + os.path.getsize(file)
                if filesize >= space_to_make:
                    break
            for idx in range(0, n+1):
                self.__delete_file(sorted_list[idx][1])

    def __get_oldest(self, possible_files: List)   -> List:
        """Private method to get a list of local files which are sorted by creation date.

        :param possible_files: Everything in directory which matches pattern.
        :type possible_files: List
        :return: Sorted list with the oldest files as first entry.
        :rtype: List
        """
        # helper
        creation_dates = []
        for file in possible_files:
            if str(file).endswith(".log"):
                continue
            # read out creation date (here: creation_time) of each file 
            creation_time = os.path.getctime(file)
            # convert to easy readable time
            creation_time = time.ctime(creation_time)
            # append to list
            creation_dates.append(creation_time)
        # zip file name and creation time
        ziped_lists = zip(creation_dates, possible_files)
        # sort for oldest
        sorted_ziped_lists = sorted(ziped_lists, key=lambda x: x[0])
        return sorted_ziped_lists
    
    def __delete_file(self, deleting_file: str) -> None:
        """Private method to delete parsed file. 

        :param deleting_file: File(path) that should be deletet.
        :type deleting_file: str
        :raises OSError: An error is raisen if files cannot be removed (arbitrary reasons).
        :raises Valueerror: If parsed string is empty.
        """
        try:
            os.remove(deleting_file)
            if self.log_entries:
                self.file_logger.info(f"File: {deleting_file} removed sucessfull")
        except OSError as error:
            if self.log_entries:
                self.file_logger.error(error)
                self.file_logger.error(f"File {deleting_file} could not be removed.")

    def _create_file_logger_obj(self, path:Union[str, Path, os.PathLike], pattern_to_log:str, filesize_limit:int):
        """Creates formatete object from python built in logging module.

        Creates a RotatingFileHandler object which logs all occuring events. Logged will be time, name of function and
        message itself. The logfile name will be created automatically by used search pattern and stored in supervised
        directory. If filesize limit is reached a new logfile will be created. NOTE: there is no stdout handler 
        implemented here. 

        :param pattern_to_log: Path of supervised directory
        :type pattern_to_log: str
        :param pattern_to_log: Pattern which is used in constrcutor of DeleteHandler class
        :type pattern_to_log: str
        :param filesize_limit: Maximum logfile size in bytes
        :type filesize_limit: int
        :return: logger object
        :rtype: logging.handlers.RotatingFileHandler
        """
        #create logger
        logger_name = pattern_to_log + "_file_logger"
        logger_obj = logging.getLogger(logger_name)
        
        file_path = Path(path) / Path(pattern_to_log + ".log") 
        print(file_path)
        #define logger
        #set logging level to lowest setting
        logger_obj.setLevel(logging.DEBUG)
        # create rotating file handler and set level to debug
        rfh = logging.handlers.RotatingFileHandler(str(file_path), maxBytes=filesize_limit, backupCount=1)
        rfh.setLevel(logging.DEBUG)
        # create sys.stderr handler
        ch_stderr = logging.StreamHandler(sys.stderr)
        # create formatter
        formatter = logging.Formatter('%(asctime)s  - %(levelname)s - %(funcName)s - %(message)s')
        # add formatter to rfh and ch_stderr
        rfh.setFormatter(formatter)
        ch_stderr.setFormatter(formatter)
        # add ch to logger
        logger_obj.addHandler(rfh)
        logger_obj.addHandler(ch_stderr)

        return logger_obj