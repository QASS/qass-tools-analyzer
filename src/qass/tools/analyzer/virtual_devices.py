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
"""Virtual devices

This module provides a simplified interface for the virtual devices of the Analyzer4D software.
The Analyzer4D software provides an interface that allows to add customized devices that are not handled by the measurement hardware.
But the data coming from those virtual devices will be handled in the same way like the time domain signal from the measurement hardware.
The data is stored in a so called "Buffer" that works based on equally distanced data.
The resulting data streams are completely compatible to other data streams in the software.

Data channels from a virtual device have to be configured in the Analyzer4D software in the multiplexer settings (Configuration->Multiplexer->Virtual input configuration).
There the devices can be assigned to measurement ports.
"""

from Analyzer.Devices import VirtDeviceInterface
from Analyzer.Core import Log_IF

# to not block the Analyzer4D software when reading data each virtual device works in its own thread.
from PySide2.QtCore import QThread, QByteArray, Slot, QElapsedTimer
from PySide2.QtWidgets import QDialog
from threading import Lock

from abc import ABC, abstractmethod
import traceback
from typing import List, Dict, Tuple
import json

from sys import version_info
if version_info.major != 3:
    raise RuntimeError('Expected Python3')
if version_info.minor <= 6:
    from collections import Sequence
else:
    from collections.abc import Sequence


class VirtualInputDevice(ABC):
    """
    VirtualInputDevice is a simplified interface for custom virtual devices in the Analyzer4D software.
    The methods marked with "abstractmethod" must be implemented.
    The other methods can be overridden if needed.

    This class is meant to be used by DeviceHandler (see below).
    The device handler implements the actual Analyzer4D interface class while using instances of this class for the communication.
    """

    def __init__(self,
                 name: str,
                 sample_rate: float,
                 normal_amp: float,
                 request_rate: float=100,
                 dont_close: bool=False):
        """instantiate a VirtualInputDevice.
        This class is an abstract base class.
        You must derive from this class and implement the abstract funtions to create a custom device.

        :param name: This is the name of the device that will also be displayed in the GUI.
        The name is used as an identifier and thus it must be unique inside one DeviceTypeCollection.
        :type name: str

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

        self._config = {
            'sample_rate': sample_rate,
            'normal_amp': normal_amp,
            'request_rate': request_rate,
            'dont_close': dont_close
            }

        self._name = name

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
        This function is called at each begin of a measurement.
        It is called even when the flag "dont_stop" is True.
        Thus you can reestablish a damaged connection if needed.

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
        This method should always clear the device's buffer containing the data when it's called.
        This is to prevent old data from persisting.

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

    @property
    def requests_per_sec(self):
        return self._config['request_rate']

    @property
    def sample_rate(self):
        return self._config['sample_rate']

    @property
    def normal_amplitude(self):
        return self._config['normal_amp']

    @property
    def dont_close(self):
        return self._config['dont_close']

    @property
    def name(self):
        return self._name

    @property
    def stream_count(self):
        return 1 if 'stream_configs' not in self._config else len(self._config['stream_configs'])

    @property
    def stream_configs(self):
        return None if 'stream_configs' not in self._config else self._config['stream_configs']

    def get_config(self):
        return self._config

    def set_config(self, config):
        required_keys = ("request_rate", "sample_rate", "normal_amp", "dont_close")
        for key in required_keys:
            if key not in config.keys():
                raise KeyError(f"Config key missing: {key}")
        self._config = config

    def apply_config(self):
        pass


class MultiStreamVirtualInputDevice(VirtualInputDevice):
    def __init__(self,
                 name: str,
                 stream_configs: Tuple[Dict[str, int]],
                 request_rate: float=100,
                 dont_close: bool=False):
        """instantiate a MultiStreamVirtualInputDevice.
        This class is an abstract base class and inherits from VirtualInputDevice.
        You must derive from this class and implement the abstract funtions to create a custom device.

        :param name: This is the name of the device that will also be displayed in the GUI.
        The name is used as an identifier and thus it must be unique inside one DeviceTypeCollection.
        :type name: str

        :param stream_configs: This is a list of configs for each stream.
        The list's length defines the number of streams provided by this device.
        The config must include at least the following keywords:
        "stream_name": A string to identify the stream (displayed)
        "sample_rate": float: The streams sample rate in Hz
        "normal_amp": The maximum expected value (used for display scaling)
        :type stream_configs: Tuple[Dict[str, int]]

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

        # The sample rate must not be 0 even if it is not used!
        super().__init__(name, 1, 0, request_rate, dont_close)

        required_keys = ("stream_name", "sample_rate", "normal_amp")
        filter_req = lambda x: x not in required_keys

        for sc in stream_configs:
            filtered_keys = list(filter(filter_req, sc))
            if filtered_keys:
                raise ValueError(f'At least one entry of stream_configs does not contain required keys {",".join(filtered_keys)}')

        self._config['stream_configs'] = stream_configs

    @abstractmethod
    def get_data(self) -> Tuple[List[float]]:
        """Fetch the data for all streams and convert them to a Tuple of List of floats.
        The tuple is expected to have stream_count elements.
        Note: Ensure that the data type is float and not np.float or anything else!
        This method should always clear the device's buffer containing the data when it's called.
        This is to prevent old data from persisting.

        :return: The lists of new values for all streams, packed into one tuple.
        The list must not contain old values!
        :rtype: Tuple[List[float]]
        """
        ...


class _DeviceThread(QThread):
    """_DeviceThread implements a QThread.
    The thread is startet when a measurement starts.
    Inside this thread communication to the device takes place.
    """
    def __init__(self, device: VirtualInputDevice):
        super().__init__()

        self.should_stop = False
        self.values = []
        self.lock = Lock()
        self.device = device

    def fetch_values(self, stream: int) -> List[float]:
        """fetch_values is called by the interface from the reading thread in the Analyzer4D software.
        It first aqcuires the lock to prevent race conditions when fetching the values.

        :return: The list of currently available values.
        :rtype: List[float]
        """
        with self.lock:
            vals = self.values[stream].copy()
            self.values[stream].clear()

        return vals

    def stop(self):
        self.should_stop = True

    def run(self):
        """The run method is implicitly called by the QThread class.
        It is executed in a seperate thread.
        The thread finishes when this function terminates.

        Exceptions caught during the execution will be logged as a popupError.
        This should lead to a fail state in the Analyzer4D software, including clearing the 'ready' output line.
        """
        try:
            request_rate = self.device.requests_per_sec

            if request_rate:
                elapsed = QElapsedTimer()
                elapsed.start()
                read_counter = 0

            self.should_stop = False
            with self.lock:
                self.values = tuple(list() for _ in range(self.device.stream_count))

            self.device.open_connection()

            # empty the data queue at start - we do not want to use old data
            if self.device.dont_close:
                self.device.get_data()


            while not self.should_stop:
                new_data = self.device.get_data()
                if not isinstance(new_data, Sequence):
                    raise ValueError(f'Device {self.device.name} get_data must return a Sequence but returned {type(new_data)}')

                if new_data:
                    first_elem = new_data[0]
                    if not isinstance(first_elem, Sequence):
                        if self.device.stream_count != 1:
                            raise ValueError(f'Device {self.device.name} get_data must return a Sequence of Sequences since it has multiple streams.')
                        with self.lock:
                            self.values[0].extend(new_data)
                    else:
                        with self.lock:
                            for idx, d in enumerate(new_data):
                                self.values[idx].extend(d)

                if request_rate:
                    read_counter += 1
                    elapsed_should = 1/request_rate * 1e9 * read_counter
                    elapsed_is = elapsed.nsecsElapsed()
                    wait_time = int((elapsed_should - elapsed_is) / 1e3)
                    if wait_time > 0:
                        QThread.usleep(wait_time)
                else:
                    self.yieldCurrentThread()

            if not self.device.dont_close:
                self.device.close_connection()
        except Exception:
            Log_IF.popupError(f'Exception caught in device thread:\n{traceback.format_exc()}')


class DeviceTypeCollection(VirtDeviceInterface):
    """DeviceClass implements the interface VirtDeviceInterface from the Analyzer4D software.
    The functions of this interface are called by the Analyzer4D software.
    This class is a plugin implementation of the interface.

    A DeviceClass is a class of hardware devices.
    Usually all devices handled by this class work similar to each other and support the same features.
    """
    def __init__(self, devices: List[VirtualInputDevice], name:str='', version:str=''):
        """
        The constructor expects a .
        The devices are expected to be of the type VirtualInputDevice.

        :param devices: List of the device. Their names are used as identifiers and have to be unique inside this DeviceTypeCollection.
        :type devices: List[VirtualInputDevice]
        :param name: The name of this device class, defaults to ''
        :type name: str, optional
        :param version: The version string of this device class implementation, defaults to ''
        :type version: str, optional
        """
        super().__init__()

        self._name = name
        self._version = version

        self._devices = {}
        for dev in devices:
            if dev.name in self._devices:
                raise ValueError('The devices` names have to be unique, but got multiple devices with the same name')
            self._devices[dev.name] = dev

        self._device_threads: Dict[_DeviceThread] = {}
        for name, dev in self._devices.items():
            self._device_threads[name] = _DeviceThread(dev)

    def init(self):
        """
        This function is called by the Analyzer4D software.
        Usually device detection takes part here.
        We assume in this implementatoin that available devices have been passed in the constructor.
        """
        pass

    def capabilities(self) -> Dict:
        """capabilites is called by the Analyzer4D software to get information about available devices and their configuration.
        Especially the sample rate and the capability of configuration dialogs is queried here.
        The config dict consists of two main keys (inputs, configdialog)
        The 'inputs' key contains an interface config with the keys (ifaceName : str, sampleRate: float, normalAmplitude: float)
        The 'configdialog' is a boolean indicating whether a QDialog will be displayed
        Missing keys in the config will

        :return: A dictionary containing information about this device class and the devices themselves.
        :rtype: Dict
        """
        interfaces_conf = []

        has_config = False
        for name, dev in self._devices.items():
            if dev.config_dialog() is not None:
                has_config = True

            int_conf = {
                'ifaceName': name,
                'sampleRate': dev.sample_rate,
                'normalAmplitude': dev.normal_amplitude,
                'streamcount': dev.stream_count
            }

            if dev.stream_configs:
                for idx, sc in enumerate(dev.stream_configs):
                    int_conf[f'streamname{idx}'] = sc["stream_name"]
                    int_conf[f'streamrate{idx}'] = sc["sample_rate"]
                    int_conf[f'streamampl{idx}'] = sc["normal_amp"]

            interfaces_conf.append(int_conf)

        config = {
            'inputs': interfaces_conf,
            'configdialog': has_config
        }
        return config

    def versionString(self) -> str:
        """versionString

        :return: The version of this device class implementation.
        :rtype: str
        """
        return self._version

    def name(self) -> str:
        """name

        :return: This device class' name.
        :rtype: str
        """
        return self._name

    def isInputAvailable(self, name: str) -> bool:
        """isInputAvailable requests to check whether the given device is available and ready for measurements.

        :param name: The device's identifier string
        :type name: str
        :return: True if the device is available and ready. False otherwise.
        :rtype: bool
        """
        if name not in self._devices:
            return False

        return self._devices[name].is_available()

    def inputCount(self) -> int:
        stream_count = sum(dev.stream_count for dev in self._devices)
        return stream_count

    def openInput(self, name: str) -> bool:
        """openInput starts the communication and the data fetching for the given device.
        This function starts the device's thread.
        All communication to the device and the data collection is done inside this thread.

        :param name: The device's identifier string
        :type name: str
        :return: True on success, False otherwise
        :rtype: bool
        """
        try:
            if not self._device_threads[name].isRunning():
                self._device_threads[name].start()
            return True
        except Exception as e:
            Log_IF.popupError(f'Exception caught during opening virtual device {name}:\n{traceback.format_exc()}')
            return False

    def closeInput(self, name: str, prepareRestart = False) -> bool:
        """closeInput requests to stop the data collection for the given device.
        In this implementation this causes the device's thread to terminate.

        :param name: The device's identifier string
        :type name: str
        :param prepareRestart: defaults to False
        :type prepareRestart: bool, optional
        :return: True on success, False otherwise
        :rtype: bool
        """
        if prepareRestart and self._device_threads[name].isRunning():
            return True

        try:
            self._device_threads[name].stop()
            deadline = 100 # ms
            if not self._device_threads[name].wait(deadline):
                Log_IF.popupError(f'Failed to close virtual device {name} within {deadline} ms - Timeout.')
                return False

            return True
        except Exception as e:
            Log_IF.popupError(f'Exception caught during closing virtual device {name}:\n{traceback.format_exc()}')
            return False

    def readInput(self, name: str, stream: int) -> List[float]:
        """readInput fetches and returns the currently available data from the given device's thread.

        :param name: The device's identifier string
        :type name: str
        :param stream:
        :type stream: int, optional
        :return: List of available new values.
        :rtype: List[float]
        """
        vals = self._device_threads[name].fetch_values(stream)
        return vals

    def getConfig(self, name: str) -> QByteArray:
        """The Analyzer4D software calls this function to make settings persistent in the database.
        This implementation converts a dictionary based configuration from the device to the QByteArray that is expected by the Analyzer4D software.

        :param name: The device's identifier string
        :type name: str
        :return: The byte array - the configuration's textual representation
        :rtype: QByteArray
        """
        try:
            config_dict = self._devices[name].get_config()
            json_str = json.dumps(config_dict)
            return json_str.encode()
        except Exception as e:
            Log_IF.popupError(f'Exception caught during getting config from virtual device {name}:\n{traceback.format_exc()}')

    def setConfig(self, name: str, data: QByteArray) -> bool:
        """setConfig is called after the device initialization to propagate saved settings from the database to the devices themselves.
        This function translates the settings from a QByteArray representation to a json dictionary.

        :param name: The device's identifier string
        :type name: str
        :param data: The byte array containing the textual representation of the device.
        :type data: QByteArray
        :return: True on success, False otherwise (if an exception has been raised)
        :rtype: bool
        """
        try:
            # There is a very nasty bug in older PySide2 / Python versions - The following crashes!
            # We have to do the conversion differently.
            #json_str = bytes(data).decode()

            json_str = ''
            for c in data:
                json_str += c.decode()

            if json_str:
                config_dict = json.loads(json_str)
                self._devices[name].set_config(config_dict)
            return True
        except Exception as e:
            Log_IF.popupError(f'Exception caught during setting config to virtual device {name}:\n{traceback.format_exc()}')
            return False

    def applyConfig(self, name: str) -> bool:
        """applyConfig is called by the Analyzer4D software to request the device to apply the config.
        This might include to communicate settings to a device.

        :param name: The device's identifier string
        :type name: str
        :return: True on success, False otherwise (if an exception has been raised)
        :rtype: bool
        """
        try:
            self._devices[name].apply_config()
            return True
        except Exception as e:
            Log_IF.popupError(f'Exception caught during config application of virtual device {name}:\n{traceback.format_exc()}')
            return False

    def createPluginDialog(self) -> QDialog:
        """createPluginDialog allows to implement a custom dialog for this device type.
        This implementation does not use this feature.
        But you can override this function by subclassing this class...

        :return: A QDialog instance.
        :rtype: QDialog
        """
        return None

    def createConfigDialog(self, name: str) -> QDialog:
        """createConfigDialog is called by the Analyzer4D software to allow the user to configurate the device.
        This mitght include file paths, IP addresses, Ports, sample rates or other device specific parameters.
        If the device implementation supports this feature it must return a QDialog instance in its implementation of config_dialog().
        This dialog is just forwarded here.

        :param name: The device's identifier string
        :type name: str
        :return: The configuration QDialog instance.
        :rtype: QDialog
        """
        try:
            return self._devices[name].config_dialog()
        except Exception as e:
            Log_IF.popupError(f'Exception caught during creation of config dialog for virtual device {name}:\n{traceback.format_exc()}')
            return None
