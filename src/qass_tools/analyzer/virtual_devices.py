"""Virtual devices

This module provides a simplified interface for the virtual devices of the Analyzer4D software.
The Analyzer4D software provices an interface that allows to add customized devices that are not handled by the measurement hardware.
But the data coming from those virtual devices will be handled in the same way like the time domain signal from the measurement hardware.
The data is stored in a so called "Buffer" that works based on equally distanced data.
The resulting data streams are completely compatible to other data streams in the software.

Data channels from a virtual device have to be configured in the Analyzer4D software in the multiplexer settings (Configuration->Multiplexer->Virtual input configuration).
There the devices can be assigned to measurement ports.
"""

from Analyzer.Devices import VirtDeviceInterface
from Analyzer.Core import Log_IF

# to not block the Analyzer4D software when reading data each virtual device works in its own thread.
from PySide2.QtCore import QThread
from threading import Lock

from abc import ABC, abstractmethod
import traceback
from typing import List, Dict

class SimpleDevice(ABC):
    """
    SimpleDevice is a simplified interface for custom virtual devices.
    The methods marked with "abstractmethod" must be implemented.
    The other methods can be overridden if needed.
    
    This class is meant to be used by DeviceHandler (see below).
    The device handler implements the actual Analyzer4D interface class while using instances of this class for the communication.
    """

    def __init__(self, 
                 sample_rate: float, 
                 normal_amp: float, 
                 request_rate: float=100, 
                 dont_close: bool=False):
        """instantiate a SimpleDevice.
        This class is an abstract base class. 
        You must to derive from this class and implement the abstract funtions to create a custom device.

        :param sample_rate: This is the sample rate that is used by the Analyzer4D software to build the Data signal stream.
        All values are assumed to have the same distance in time.
        :type sample_rate: float

        :param normal_amp: This is the maximum value that this device will provide.
        This is used by the Analyzer4D software for the correct scaling.
        :type normal_amp: float

        :param request_rate: How often the get_data() should be called?, defaults to 100 - meaning 100 calls of get_data() in a second.
        If zero or None the device communication thread will not sleep but only yieldCurrentThread.
        This might cause issues since the python interpreter is heavily used by this interface.
        :type request_rate: float, optional

        :param dont_close: If True the function open_connection() will be called as early as possible and close_connection() will be called as late as possible.
        The device connection will not be closed between different processes.
        If False the method open_connection() will be called at the beginning of each measurement and close_connection() will be called at the end of each measurement.
        Defaults to False.
        :type dont_close: bool, optional
        """        
           
        self.__sample_rate = sample_rate
        self.__normal_amp = normal_amp
        self.__request_rate = request_rate
        self.dont_close = dont_close
    
    @abstractmethod
    def is_available(self) -> bool:
        """is_available should indicate whether its possible to establish a connection to the device.

        :return: True if the device is available and ready for measurements, False otherwise. 
        :rtype: bool
        """
        ...
    
    @abstractmethod
    def open_connection(self):
        """open_connection() will be called before a measurement.
        The communication to the device should be setup in this function.
        It is assumed that its save to call get_data after this function returned without error.

        raise an exception if needed. It will be handled by the wrapping class DeviceHandler.
        """
        ...
    
    @abstractmethod
    def close_connection(self):
        """close_connection() will be called to close the connection to the device (usually at the end of a measurement).
        The communication to the device should be completely cleaned up in this function.
        It is assumed that its save to call open_connection() again after this function returned without error.

        raise an exception if needed. It will be handled by the wrapping class DeviceHandler.
        """
        ...
        
    @abstractmethod
    def get_data(self) -> List[float]:
        """Fetch the data from the device and convert it to a List of floats.
        Note: Ensure that the data type is float and not np.float or anything else!
        
        :return: The list of new values. The list must not contain old values!
        :rtype: List[float]
        """
        ...
    
    # overide the functions below if needed
    def init_device(self):
        return None
    
    def config_dialog(self):
        """If this function returns a QDialog this will be displayed in the Analyzer4D software to setup the device.
        The settings button will only be available in the software if at least one device provides a QDialog and not None in this funciton.

        :return: your custom config dialog. Defaults to None.
        :rtype: _type_
        """
        return None
    
    def requests_per_sec(self):
        return self.__request_rate
    
    def sample_rate(self):
        return self.__sample_rate
    
    def normal_amplitude(self):
        return self.__normal_amp


class _DeviceThread(QThread):
    def __init__(self, device: SimpleDevice):
        super().__init__()

        self.should_stop = False
        self.values = []
        self.lock = Lock()
        self.device = device
    
    def fetch_values(self):
        with self.lock:
            vals = self.values
            self.values = []
        
        return vals
    
    def stop(self):
        self.should_stop = True
    
    def run(self):
        try:
            self.should_stop = False
            with self.lock:
                self.values = []
            
            if not self.device.dont_close:
                self.device.open_connection()
            
            # empty the data queue at start - we do not want to use old data
            self.device.get_data()
            
            request_rate = self.device.requests_per_sec()
            
            while not self.should_stop:
                new_data = self.device.get_data()
                with self.lock:
                    self.values.extend(new_data)

                if request_rate:
                    QThread.usleep(1/request_rate * 1e6)
                else:
                    self.yieldCurrentThread()
            
            if not self.device.dont_close:
                self.device.close_connection()
        except Exception:
            Log_IF.popupError(f'Exception caught in device thread:\n{traceback.format_exc()}')


class DeviceHandler(VirtDeviceInterface):
    def __init__(self, devices: Dict[str, SimpleDevice], name:str='', version:str=''):
        super().__init__()
        
        self._devices = devices
        self._name = name
        self._version = version
        
        self._device_threads = {}
        
        for name, dev in self._devices.items():
            self._device_threads[name] = _DeviceThread(dev)
    
    def init(self):
        pass
    
    def capabilities(self):
        interfaces_conf = []
        
        has_config = False
        for name, dev in self._devices.items():
            if dev.config_dialog() is not None:
                has_config = True
            
            int_conf = {
                'ifaceName': name,
                'sampleRate': dev.sample_rate(),
                'normalAmplitude': dev.normal_amplitude()
            }
            interfaces_conf.append(int_conf)
        
        config = {
            'inputs': interfaces_conf,
            'configdialog': has_config
        }
        return config
    
    def versionString(self):
        return self._version
    
    def name(self):
        return self._name
    
    def isInputAvailable(self, name):
        if name not in self._devices:
            return False
        
        return self._devices[name].is_available()
    
    def inputCount(self):
        return len(self._devices)
    
    def openInput(self, name):
        try:
            self._device_threads[name].start()
            return True
        except Exception:
            return False
    
    def closeInput(self, name, prepareRestart = False):
        try:
            self._device_threads[name].stop()
            return True
        except Exception:
            return False
    
    def readInput(self, name, stream=0):
        return self._device_threads[name].fetch_values()
