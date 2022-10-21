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
from Analyzer.Devices import VirtDeviceInterface, VirtDeviceManager_IF
from qass.tools.analyzer.virtual_devices import VirtualInputDevice, DeviceTypeCollection

from typing import List
import numpy as np
import time
import os

# BEGIN config dialog GUI
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, QIODevice
from PySide2.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

def load_ui_file(ui_file_name: str):
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        raise RuntimeError(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
    loader = QUiLoader()
    widget = loader.load(ui_file)
    ui_file.close()
    if widget is None:
        raise RuntimeError(f"Could not load {ui_file_name}: {loader.errorString()}")
    return widget


class MyDevConfigDialog(QDialog):
    def __init__(self, device):
        super().__init__()
        self._device = device
        self.setWindowTitle(self._device.name)

        ui_file_name = os.path.dirname(__file__) + "/virtual_device_config_dialog.ui"
        self.ui = load_ui_file(ui_file_name)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        lay = QVBoxLayout()
        lay.addWidget(self.ui)
        lay.addWidget(button_box)
        self.setLayout(lay)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.accepted.connect(self.store_config)

        self.load_config()

    def store_config(self):
        config = {
            'sample_rate': self.ui.touchspinbox_sample_rate.value(),
            'request_rate': self.ui.touchspinbox_request_rate.value(),
            'normal_amp': self.ui.touchspinbox_normal_amp.value(),
            'dont_close': self.ui.touchcheck_dont_close.isChecked(),
            }

        dev_cfg = self._device.get_config()
        # update config:
        for key, val in config.items():
            dev_cfg[key] = val

        self._device.set_config(dev_cfg)

    def load_config(self):
        config = self._device.get_config()
        self.ui.touchspinbox_sample_rate.setValue(config['sample_rate'])
        self.ui.touchspinbox_request_rate.setValue(config['request_rate'])
        self.ui.touchspinbox_normal_amp.setValue(config['normal_amp'])
        self.ui.touchcheck_dont_close.setChecked(config['dont_close'])
# END config dialog GUI


# BEGIN Device implementation
class MyDevice(VirtualInputDevice):
    def __init__(self, name:str, mean:float, std:float):
        self._mean = mean
        self._std = std
        self._start_time = None

        super().__init__(name, 500, mean + 3*std, request_rate=100)

    def open_connection(self):
        self._start_time = time.time()
        self._values_provided = 0

    def get_data(self) -> List[float]:
        time_elapsed = time.time() - self._start_time
        values_needed = int(time_elapsed * self.sample_rate) - self._values_provided

        self._values_provided += values_needed
        return [float(v) for v in np.random.normal(self._mean, self._std, values_needed)]

    def is_available(self) -> bool:
        return True

    def close_connection(self):
        pass

    def config_dialog(self):
        return MyDevConfigDialog(self)
# END Device implementation


# BEGIN Device registration in the Analyzer4D software
dev_1 = MyDevice('dev1', 50, 10)
dev_2 = MyDevice('dev2', 1000, 10)
devices = [dev_1, dev_2]

# This object implements the virtual device interface of the Analyzer4D software.
dev_handler = DeviceTypeCollection(devices)

try:
    # First remove the device type if it already exists
    VirtDeviceManager_IF.removeVirtualDevice('MyDev')
except Exception:
    pass
# Register this device type
VirtDeviceManager_IF.addVirtualDevice(dev_handler, 'MyDev')
# Reinitialize all virtual input devices
VirtDeviceManager_IF.initVirtualDevices()
# BEGIN Device registration in the Analyzer4D software
