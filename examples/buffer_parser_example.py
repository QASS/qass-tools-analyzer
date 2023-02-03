#!/usr/bin/env python

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

from qass.tools.analyzer import buffer_parser as bp

import matplotlib.pyplot as plt
import numpy as np

data_path = '/data1/MyProject/'
file_path = data_path + 'MyProject_00003p27420c0b01_dump_00.000'

with bp.Buffer(file_path) as buff:
    print(buff.process)
    print(buff.datamode.name)
    arr = buff.getArray()

vmax = np.percentile(arr, 97)
plt.imshow(arr.T, cmap='jet', origin='lower', aspect='auto', vmax=vmax)
plt.show()
