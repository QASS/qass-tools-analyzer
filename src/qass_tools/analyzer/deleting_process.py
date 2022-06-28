# import modules
import time
import os
import glob
from typing import List
import shutil

try:
    from Analyzer.Core import Log_IF
except:
    pass

__all__ = ["DeleteHandler"]

class DeleteHandler():
    """DeleteHandler Class with different functionalities to delete local files on disk. 
    
    With an instance of this class a specific deleting-pattern and path (for the files) will be associated. The programm always looks for the oldest versions of files which match with the pattern.
    Files will be deletet until the maximum amount of allowed files is reached or enough disk space is free. This class stands for now on its own. With a def main() syntacs it will be executed by programm start.
    
    :param path: Local directory path.
    :type path: str
    :param pattern: Searched pattern.
    :type pattern: str
    """
    def __init__(self, path: str, pattern: str) -> None:
        """Constructor to connect a specific local directory path with a specific pattern parsed.

        Provided functions can be applied later for each combination. Pattern has to be according to the rules used by Unix shell (used glob module is based on that). In the following Unix Shell rules are provided:
        | Pattern | Meaning                               | Example                                                                              |
        | ------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
        | *	      | Matches everything	                  | *.pdf matches all files with the pdf extension                                       |
        | ?	      | Matches any single character	      | sales/??.jpeg matches all files with two characters long present in the sales folder |
        | []	  | Matches any character in the sequence |	[psr]* matches all files starting with the letter p, s, or r                         |
        | [!]	  | Matches any character not in sequence |	[!psr]* matches all files not starting with the letter p, s, or r                    |
        
        For a literal match, wrap the meta-characters in brackets. For example, '[?]' matches the character '?'    

        :param path: Local directory path.
        :type path: str
        :param pattern: Searched pattern.
        :type pattern: str
        """
        self.path = path  
        self.pattern = pattern
        
    def delete_by_amount(self, max_amount: int) -> None:
        """Provided function to delete files based on file amount in location if amount overruns defined limit.

        :param max_amount: Maximum amount (limit) of files allowed in this directory which are match pattern.
        :type max_amount: int
        :raises OSError: Exception is raised if deleting process cannot be compelted. Either because there are not enough files that match pattern to satisfy limit or because any other wild error appears. 
        """
        # read out amount of files in directory
        dir_amount = len(os.listdir(self.path))
        # calc how many files have to be deletet in order to satisfy limit
        amount_to_delete = int(dir_amount) - max_amount
        # if there are any files to delete:

        if amount_to_delete > 0:
            # search for files in directory which match pattern
            full_path = str(self.path / self.pattern)
            delete_list = glob.glob(full_path) # delete_list is saved with full path
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            
            try:
                for idx in range(0, amount_to_delete):
                    self.__delete_file(sorted_list[idx][1])
                print("Deleting successfull")
            except OSError as e:
                #Log_IF().error(f"Deleting process could not be completed. Check your setted Limit and your Files.")
                print(e)
                print("Deleting process could not be completed. Check your setted Limit and your Files.")
        
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
            full_path = str(self.path / self.pattern)
            delete_list = glob.glob(full_path) # delete_list is saved with full path# sort list for oldest files
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            # helper
            filesize = 0
            #n = -1
            for n, (date, file) in enumerate(sorted_list):
                filesize = filesize + os.path.getsize(file)
                if filesize >= space_to_make:
                    break
            try:
                for idx in range(0, n+1):
                    self.__delete_file(sorted_list[idx][1])
                    print("Deleting successfull")
            except OSError as e:
                #Log_IF().error(f"Deleting process could not be completed. Check your setted Limit and your Files.")
                print(e)
                print("Deleting process could not be completed. Check your setted Limit and your Files.")

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

        :param deleting_file: _description_
        :type deleting_file: str
        :raises OSError: An error is raisen if files cannot be removed (arbitrary reasons).
        :raises Valueerror: If parsed string is empty.
        """
        try:
            if deleting_file == "":
                raise ValueError("No files to remove")
            else:
                os.remove(deleting_file)
                print("File removed sucessfully")
        except OSError as error:
            print(error)
            print("File could not be removed")


# syntacs for automatic appling of programm
def main():
    """ Function to execute codes below by executing complete script. That means if complete code-file gets started the lines in this function will be executed."""
    # define path
    PATH = "/home/opti/tmp_dir/"
    # create instance
    file_deleter = DeleteHandler(PATH, "*.txt")
    # delete by 90% used disk space
    file_deleter.delete_by_amount(2)

if __name__ == "main":
    main()
