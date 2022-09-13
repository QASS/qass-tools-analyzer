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
from Analyzer.OpNet import SearchInfo_IF, RunTimeInfo_IF, ConnectorOut_Py_IF
from Analyzer.Core import Buffer_Py_IF
import random

class SearchIndicator:
    """
    The class SearchIndicator provides a simple interface to update Search info markers in the OpenGL area.
    Each SearchIndicator instance creates its own rectangle that will be displayed.

    A search info rectangle can be useful to display the progress of the analysis for the current process.
    """
    def __init__(self, rti: RunTimeInfo_IF, out_connector: ConnectorOut_Py_IF, duration_ns: int=1e6, label: str="analysis", start_fband: int=None, end_fband: int=None) -> None:
        """
        Constructor for SearchIndicator.

        :param rti: The runtime information object of the operator network. It provides information about the current analysis.
        :type rti: RunTimeInfo_IF

        :param out_connector: The connector object of type Search Info that can handle and propagate the created SearchInfo_IF() objet.
        :type out_connector: ConnectorOut_Py_IF

        :param duration_ns: duration of the analysis window (This is the width of the displayed rectangle).
        :type duration_ns: int

        :param label: An arbitrary string - displayed next to the rectangle in the OpenGL area.
        :type label: str

        :param start_fband:  Optional index for the first frequency band covered by the rectangle.

        :param end_fband:  Optional index for the first frequency band covered by the rectangle.
        """
        self._stream = None
        self._rti = rti
        self._label = label
        self._duration = duration_ns
        self._ref_id = random.randint(1, 2^31 -1)
        self._out_connector = out_connector
        self._start_fband = start_fband
        self._end_fband = end_fband

    def process_init(self, stream: Buffer_Py_IF):
        """
        The function process_init resets the internal state of the object.
        It creates a new instance of type SearchInfo_IF fitting the new stream.
        """
        self._stream = stream

        self._si = SearchInfo_IF()
        self._si.setSearchBuffer(self._stream)
        self._si.setDuration(int(self._duration))
        self._si.setLabel(self._label)
        self._si.setRefID(int(self._ref_id))
        self._si.setFStartHz(stream.getLowFrequency() if not self._start_fband else self._start_fband * stream.getFrqPerBand())
        self._si.setFEndHz(stream.getHighFrequency() if not self._end_fband else self._end_fband * stream.getFrqPerBand())

    def tick(self):
        """
        The function tick has to bee called in every iteration of the operator network during the phase process_run().
        """
        self._si.setTrackingTime(self._rti.getCurrentTime())
        self._out_connector.setOutputValue(self._si)
