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
from Analyzer.Core import Buffer_Py_IF, RunTimeInfo_IF
from typing import Tuple, List


class InputObserver:
    """"
    The InputObserver class can observe a Analyzer4D data stream for toggles of input bits.
    Its configuration is a list of tuples to observe different input bits.
    Input bits can be observed for high or low states (True/False).
    Furthermore an offset after the end of a range can be configured.

    When a finished period for an input has been detected the callback function is called.

    In each clock cycle the function tick() must be called with the current operator network time.
    process_start() is called to reset the InputObserver for a new process.
    process_end() is called to finish all currently detected periods. The callback is then called even if the delay did not expire.
    """

    def __init__(self, rti: RunTimeInfo_IF, inputs: List[Tuple[int, int, bool, int]], callback):
        """
        :param rti: Operator network's runtime info object. This object contains information about the current analysis.
        :type rti: RunTimeInfo_IF

        :param inputs: list of input oberserver configurations.
        Each tuple in the list must habe the following form: (byte, bit, state [True/False], delay [in nanoseconds])

        :param callback: The callback function is called.
        Its signature must be: ((byte, bit, state, delay), start_time, end_time).
        The times are provided in nanoseconds.
        """
        self._rti = rti
        self._inputs = inputs
        self._stream = None
        self._current_input_times = None
        self._finished_ranges = None
        self._last_spec = None
        self._callback = callback

    def process_init(self, stream: Buffer_Py_IF) -> None:
        """
        The function process_start must be called in the phase eval_process_init() of the operator network.

        :param stream: The stream that should be monitored for input changes.
        Ensure that the stream has an appropriate resolution for your demands.
        """
        self._stream = stream
        self._current_input_times = [None for _ in self._inputs]
        self._last_spec = 0
        self._finished_ranges = []

    def tick(self, ignore_getIO_exception: bool = False) -> None:
        """
        This function must be called in the phase eval_process_run() of the operator network.
        It is called for every single spectrum and checks the current input state.
        """
        spec_duration = self._stream.getSpecDuration()
        curr_spec = int(self._rti.getCurrentTime() // spec_duration)
        for spec in range(self._last_spec, curr_spec):
            stream_pos = spec * self._stream.getFrqBandCount()
            for idx, (byte, bit, state, delay) in enumerate(self._inputs):
                try:
                    curr_state = self._stream.getIO_inputs(stream_pos, byte, bit)
                except Exception as exc:
                    if ignore_getIO_exception:
                        break
                    else:
                        raise exc

                if curr_state == state and self._current_input_times[idx] is None:
                    self._current_input_times[idx] = spec * spec_duration
                elif curr_state != state and self._current_input_times[idx] is not None:
                    self._finished_ranges.append((
                        (byte, bit, state, delay),
                        self._current_input_times[idx],
                        spec * spec_duration + delay
                        ))
                    self._current_input_times[idx] = None

            exec_ranges = [(cfg, start, end) for cfg, start, end in self._finished_ranges if end <= spec * spec_duration]
            if exec_ranges:
                self._finished_ranges = [(cfg, start, end) for cfg, start, end in self._finished_ranges if end > spec * spec_duration]

            for cfg, start, end in exec_ranges:
                self._callback(cfg, start, end)

        self._last_spec = curr_spec

    def process_end(self) -> None:
        """
        This function must be called in the phase eval_process_end() of the operator network.
        It will finish all currently opened ranges and call the callback for delayed ranges even if the delay has not expired yet.
        """
        self.tick(ignore_getIO_exception=True)

        for cfg, start, end in self._finished_ranges:
            self._callback(cfg, start, self._rti.getCurrentTime())

        for idx, (byte, bit, state, delay) in enumerate(self._inputs):
            if self._current_input_times[idx] is not None:
                self._callback((byte, bit, state, delay), self._current_input_times[idx], self._rti.getCurrentTime())
