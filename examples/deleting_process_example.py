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
from qass.tools.analyzer import deleting_process
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