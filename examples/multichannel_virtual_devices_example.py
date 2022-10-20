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
from Analyzer.Devices import VirtDeviceManager_IF
from qass.tools.analyzer import virtual_devices
from importlib import reload
reload(virtual_devices)
MultiStreamVirtualInputDevice, DeviceTypeCollection = virtual_devices.MultiStreamVirtualInputDevice, virtual_devices.DeviceTypeCollection

from typing import List, Tuple, Dict
import numpy as np
import time
import os



# BEGIN Device implementation
class MultiStreamDevice(MultiStreamVirtualInputDevice):
    def __init__(self, name:str, stream_configs: Tuple[Dict[str, int]], mean_stds: Tuple[float, float]):
        self._mean_stds = mean_stds
        self._start_time = None

        super().__init__(name, stream_configs)

    def open_connection(self):
        self._start_time = time.time()
        self._values_provided = [0] * len(self._mean_stds)

    def get_data(self) -> List[float]:
        time_elapsed = time.time() - self._start_time
        
        new_vals = []
        for idx, (cfg, (mean, std)) in enumerate(zip(self.stream_configs, self._mean_stds)):
            values_needed = int(time_elapsed * cfg['sample_rate']) - self._values_provided[idx]
            new_vals.append([float(v) for v in np.random.normal(mean, std, values_needed)])
            self._values_provided[idx] += values_needed
        return new_vals

    def is_available(self) -> bool:
        return True

    def close_connection(self):
        pass
# END Device implementation

mean_stds = ((500, 2), (10, 1), (100, 200))

mc_configs = [
    {
        'stream_name': 'Stream 0',
        'sample_rate': 100,
        'normal_amp': mean_stds[0][0] + 3 * mean_stds[0][1]
    },
    {
        'stream_name': 'Stream 1',
        'sample_rate': 200,
        'normal_amp': mean_stds[1][0] + 3 * mean_stds[1][1]
    },
    {
        'stream_name': 'Stream 2',
        'sample_rate': 1000,
        'normal_amp': mean_stds[2][0] + 3 * mean_stds[2][1]
    },
]

# BEGIN Device registration in the Analyzer4D software
dev_1 = MultiStreamDevice('dev1', mc_configs, mean_stds)
devices = [dev_1]

# This object implements the virtual device interface of the Analyzer4D software.
dev_handler = DeviceTypeCollection(devices)

try:
    # First remove the device type if it already exists
    VirtDeviceManager_IF.removeVirtualDevice('MultiStreamDev')
except Exception:
    pass
# Register this device type
VirtDeviceManager_IF.addVirtualDevice(dev_handler, 'MultiStreamDev')
# Reinitialize all virtual input devices
VirtDeviceManager_IF.initVirtualDevices()
# BEGIN Device registration in the Analyzer4D software
