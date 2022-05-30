# import modules
import time
import os
import glob
from typing import List
import shutil

__all__ = ["DeleteHandler"]

class DeleteHandler():
    """ DeleteHandler Class with different functionalities to delete local files on disk. With an instance of this class a specific deleting-pattern
    and path (for the files) will be associated. The programm always looks for the oldest versions of files which match with the pattern.
    Files will be deletet until the maximum amount of allowed files is reached or enough disk space is free. This class stands for now on its own.
    With a def main syntacs it will be executed by programm start."""
    def __init__(self, path, pattern) -> None:
        """ Each instance of this class connects a specific local path with a specific deleting pattern. Provided functions can be applied later for each combination.
        Pattern has to be according to the rules used by Unix shell (used glob module is based on that). In the following Unix Shell rules are provided:
        
        Pattern     Meaning                                     Example
        *	        Matches everything	                        *.pdf matches all files with the pdf extension
        ?	        Matches any single character	            sales/??.jpeg matches all files with two characters long present in the sales folder
        []	        Matches any character in the sequence	    [psr]* matches all files starting with the letter p, s, or r
        [!]	        Matches any character not in sequence	    [!psr]* matches all files not starting with the letter p, s, or r
        For a literal match, wrap the meta-characters in brackets. For example, '[?]' matches the character '?'
        """
        self.path = path  
        self.pattern = pattern
        
    def delete_by_amount(self, max_amount: int):
        """ Provided function to delete files if file amount in opath location overruns defined limit. Limit is given as an integer in function parameters.
        Exception is raised if deleting process cannot be compelted. Either because there are not enough files that match pattern to satisfy 
        limit or because any other wild error appears """
        # read out amount of files in directory
        dir_amount = len(os.listdir(self.path))
        # calc how many files have to be deletet in order to satisfy limit
        amount_to_delete = dir_amount - max_amount
        # if there are any files to delete:
        if amount_to_delete > 0:
            # search for files in directory which match pattern
            delete_list = glob.glob(self.path + self.pattern) # delete_list is saved with full path
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            
            try:
                for idx in range(0, amount_to_delete):
                    self.__delete_file(sorted_list[idx][1])
            except:
                # raise exception
                print("Deleting process could not be completed. Check your set Limit and your Files.")

            
    def delete_by_disk_space(self, disk_usage_limit: float):
        """ Provided function to delete by disk space. As parameter the maximum disk usage as part of a whole is entered as float. Function has no own 
        exception. If a error occurs its root is in actual deleting function."""
        # read out currently used disk usage
        disk_usage = shutil.disk_usage(self.path)
        # help to debug: disk_usage[0] = total // disk_usage[1] = used // disk_usage[2] = free
        # calc free space that is required based on user limit
        target_free_space = disk_usage[0] * (1 - disk_usage_limit)
        # calc therefore required space
        space_to_make =  target_free_space - disk_usage[2]
        
        if space_to_make > 0:
            # search for files in directory which match pattern
            delete_list = glob.glob(self.path + self.pattern) # delete_list is saved with full path
            # sort list for oldest files
            sorted_list = self.__get_oldest(delete_list)
            # helper
            filesize = 0
            n = -1
            for n, (date, file)in enumerate(sorted_list):
                filesize = filesize + os.path.getsize(file)
                if filesize >= space_to_make:
                    break
            for idx in range(0, n+1):
                self.__delete_file(sorted_list[idx][1])


    def __get_oldest(self, possible_files: List)   -> List:
        """ Private function to get a list of local files which are sorted by creation date. As possible files everythin is parsed which match
        deleting pattern. As return it gives a list a sorted list with the oldest files as first entry."""
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
    
    def __delete_file(self, deleting_file: str):
        """ Private function to delete given files. An error is raisen if files cannot be removed or if parsed string is empty."""
        try:
            if deleting_file == "":
                print("No files to remove")
            else:
                os.remove(deleting_file)
                print("File removed sucessfully")
        except OSError as error:
            print(error)
            print("File could not be removed")


# syntacs for automatic appling of programm
def main():
    """ Function to execute codes below by executing complete script. Means if complete code-file gets started the lines in this function will be executed."""
    # define path
    PATH = "./"
    # create instance
    file_deleter = DeleteHandler(PATH, "*.npy")
    # delete by 90% used disk space
    file_deleter.delete_by_disk_space(.90)

if __name__ == "main":
    main()

# test script
# PATH = "/home/opti/Oli_develop_deleting-function/"
# pattern = "40*[8]*"

# create instance
# delete_master = DeleteHandler(PATH, pattern)

# delete_master.delete_by_amount(20)