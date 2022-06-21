from qass_tools.analyzer import deleting_process
"""Therefore this is a standalone python programm to call out of a batch file or so. As example the required def main is shown."""
# syntacs for automatic appling of programm
def main():
    """ Function to execute codes below by executing complete script. That means if complete code-file gets started the lines in this function will be executed."""
    # define path
    PATH = "opti/home/deleteAll/"
    # create instance
    file_deleter = deleting_process.DeleteHandler(PATH, "*.npy")
    # delete by 90% used disk space
    file_deleter.delete_by_disk_space(.90)

if __name__ == "main":
    main()