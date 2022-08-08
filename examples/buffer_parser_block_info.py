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
buff_path = '/data1/MyProject/raw2/MyProject_00008p71840c1b02_dump_00.000'

import qass_tools.analyzer.buffer_parser as bp

with bp.Buffer(buff_file) as buff:
    column_list = ['times', 'spectrums', 'inputs']
    meta_info = buff.block_infos(columns = column_list, changes_only=True)
    # ---- Here you already got the meta info. Below is just an example what you can do with it.
    
    
    #here you can filter for example you could check for a certain io values
    io_should_be = 5
    for i, mi in enumerate(meta_info):
        if mi[2] == io_should_be:
            # the start spec is in the second column of this row:
            start_idx = mi[1]
            # the end spec is in the first column of the next row:
            end_idx = meta_info[i+1, 1]
            
            data = buff.get_data(start_idx, end_idx)
            #do something with the data in this region
    

