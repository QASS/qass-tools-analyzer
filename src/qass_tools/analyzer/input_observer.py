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
from Analyzer.Core import Buffer_Py_IF
from Analyzer.OpNet import RunTimeInfo_IF
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

    def __init__(self, rti: RunTimeInfo_IF, inputs: List[Tuple[int, int, bool, int]], callback, update_time_ms: int = None):
        """
        :param rti: Operator network's runtime info object. This object contains information about the current analysis.
        :type rti: RunTimeInfo_IF

        :param inputs: list of input oberserver configurations.
        Each tuple in the list must habe the following form: (byte, bit, state [True/False], delay [in nanoseconds])
        :type inputs: List[Tuple[int, int, bool, int]]

        :param callback: The callback function is called.
        Its signature must be: ((byte, bit, state, delay), start_time, end_time).
        The times are provided in nanoseconds.

        :param update_time_ns: declares how often the IO input state is checked for changes.
        :type: int
        """
        self._rti = rti
        self._inputs = inputs
        self._stream = None
        self._current_input_times = None
        self._finished_ranges = None
        self._last_spec = None
        self._callback = callback
        self._spec_duration = None
        self._frq_band_count = None
        self._update_time_ms = update_time_ms

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
        self._spec_duration = stream.getSpecDuration()
        self._frq_band_count = stream.getFrqBandCount()
        if self._update_time_ms is None:
            io_specs_updates_raw = 15  # For hardware reasons the Optimizer4D records io changes every 15 raw specs.
            self._stream_update_specs = max(1, io_specs_updates_raw / stream.getCompressionTime()))
        else:
            self._stream_update = self._update_time_ms * 1e6 / self._spec_duration()

    def tick(self, ignore_getIO_exception: bool = False) -> None:
        """
        This function must be called in the phase eval_process_run() of the operator network.
        It is called for every single spectrum and checks the current input state.

        :param ignore_getIO_exception:
        If True exceptions raised by missing IO information in the last specs of a buffer are ignored.
        Otherwise they will be reraised.

        :type ignore_getIO_exception: bool
        """
        spec_duration = self._spec_duration
        curr_spec = int(self._rti.getCurrentTime() // spec_duration)

        specs = np.arange(self._last_spec, curr_spec, self._stream_update)
        if not len(specs):
            self._last_spec = float(specs[-1])
        specs = specs.astype(int)
        for spec in specs:
            stream_pos = spec * self._frq_band_count
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
