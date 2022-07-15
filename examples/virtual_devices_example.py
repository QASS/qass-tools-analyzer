from Analyzer.Devices import VirtDeviceInterface, VirtDeviceManager_IF
from qass_tools.analyzer.virtual_devices import VirtualInputDevice, DeviceTypeCollection

from typing import List
import numpy as np
import time

class MyDevice(VirtualInputDevice):
    def __init__(self, mean, std):
        self._mean = mean
        self._std = std
        self._start_time = None
        
        super().__init__(500, mean + 3*std, request_rate=100)
    
    def open_connection(self):
        self._start_time = time.time()
        self._values_provided = 0
    
    def get_data(self) -> List[float]:
        time_elapsed = time.time() - self._start_time
        values_needed = int(time_elapsed * self.sample_rate()) - self._values_provided
        
        self._values_provided += values_needed
        return [float(v) for v in np.random.normal(self._mean, self._std, values_needed)]
    
    def is_available(self) -> bool:
        return True
    
    def close_connection(self):
        pass
    


dev_1 = MyDevice(50, 10)
dev_2 = MyDevice(1000, 10)

devices = {
    'dev1': dev_1,
    'dev2': dev_2
    }

dev_handler = DeviceTypeCollection(devices)

try:
    VirtDeviceManager_IF.removeVirtualDevice('MyDev')
except Exception:
    pass
VirtDeviceManager_IF.addVirtualDevice(dev_handler, 'MyDev')
VirtDeviceManager_IF.initVirtualDevices()
