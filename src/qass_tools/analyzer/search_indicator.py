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
from Analyzer.OpNet import SearchInfo_IF, RunTimeInfo_IF
from Analyzer.Core import Buffer_Py_IF


class SearchIndicator:
    def __init__(self, rti, out_connector, duration=1e6, label="analysis", ref_id=5, start_fband=None, end_fband=None) -> None:
        self._stream = None
        self._rti = rti
        self._label = label
        self._duration = duration
        self._ref_id = ref_id
        self._out_connector = out_connector
        self._start_fband = start_fband
        self._end_fband = end_fband
 
    def process_start(self, stream: Buffer_Py_IF):
        self._stream = stream
        
        self._si = SearchInfo_IF()
        self._si.setSearchBuffer(self._stream)
        self._si.setDuration(int(self._duration))
        self._si.setLabel(self._label)
        self._si.setRefID(int(self._ref_id))
        self._si.setFStartHz(stream.getLowFrequency() if not self._start_fband else self._start_fband * stream.getFrqPerBand())
        self._si.setFEndHz(stream.getHighFrequency() if not self._end_fband else self._end_fband * stream.getFrqPerBand())
        
    def tick(self):
        self._si.setTrackingTime(self._rti.getCurrentTime())
        self._out_connector.setOutputValue(self._si)
