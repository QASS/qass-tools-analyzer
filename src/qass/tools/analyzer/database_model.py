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
# coding: utf-8
from sqlalchemy import CHAR, Column, DateTime, Float, ForeignKey, Index, LargeBinary, String, TIMESTAMP, Text, text, create_engine
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, LONGTEXT, MEDIUMBLOB, MEDIUMTEXT, TINYINT, JSON
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class AnalyzerDB:

    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind = engine)
        self._active_session = None

    def __enter__(self):
        '''
        returns a sqlalchemy Session instance that can be used for querying
        '''
        self._active_session = self.create_session()
        return self._active_session

    def __exit__(self, *args, **kwargs):
        self._active_session.close()

    @staticmethod
    def create_engine(ip = 'localhost', db = 'opti', db_url = None):
        '''
        Create an engine for the Analyzer database schema to connect to an Optimizer

        :param str ip: the ip adress of the device
        :param str db: the name of the database you want to connect to 
        :param str db_url: the complete db_url
        :returns: An engine object that can be used to create a connection
        '''
        if db_url is None:
            db_url = f'mysql+pymysql://opti:mizerdb@{ip}/{db}'
        engine = create_engine(db_url)
        return engine 
    
    def create_session(self):
        return self.Session()


class AgglomerativeClusterTreeTable(Base):
    __tablename__ = 'agglomerative_cluster_tree_table'
    __table_args__ = {'comment': 'information about result tree of agglomerative clustering'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    clustering_id = Column(BIGINT(20), nullable=False)
    parent_id = Column(BIGINT(20), nullable=False, index=True)
    leaf_json = Column(Text, nullable=False)


class BufferSnippet(Base):
    __tablename__ = 'buffer_snippet'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    result_id = Column(INTEGER(11), nullable=False)
    origin_bufferid = Column(BIGINT(20), nullable=False, index=True)
    origin_time_start = Column(BIGINT(20), nullable=False)
    origin_time_end = Column(BIGINT(20), nullable=False)
    origin_frq_begin = Column(INTEGER(11), nullable=False)
    origin_frq_end = Column(INTEGER(11), nullable=False)
    snippet_bufferid = Column(BIGINT(20), nullable=False)
    snippet_time_start = Column(BIGINT(20), nullable=False)
    snippet_time_end = Column(BIGINT(20), nullable=False)
    snippet_frq_begin = Column(INTEGER(11), nullable=False)
    snippet_frq_end = Column(INTEGER(11), nullable=False)


class Cluster(Base):
    __tablename__ = 'cluster'
    __table_args__ = {'comment': 'similarity relations between results'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    cluster_set_id = Column(BIGINT(20), nullable=False, index=True)
    number = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    created = Column(DateTime, nullable=False, index=True)
    comment = Column(String(256), server_default=text("'0'"))
    paramjson = Column(String(2000), server_default=text("''"))
    name = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    pattern_id = Column(BIGINT(20), nullable=False)
    buffer_id = Column(BIGINT(20), nullable=False)


class ClusterItem(Base):
    __tablename__ = 'cluster_item'
    __table_args__ = {'comment': 'similarity relations between results'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    cluster_id = Column(BIGINT(20), nullable=False, index=True)
    result_id = Column(BIGINT(20), nullable=False)
    created = Column(DateTime, nullable=False, index=True)
    rr_similarity = Column(Float(asdecimal=True), nullable=False)
    hc_result = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    item_rank = Column(Float(asdecimal=True), nullable=False, index=True)
    comment = Column(String(256), server_default=text("''"))
    paramjson = Column(String(2000), server_default=text("''"))
    usertype = Column(String(32), server_default=text("'unknown'"))


class ClusterSet(Base):
    __tablename__ = 'cluster_set'
    __table_args__ = {'comment': 'similarity relations between results'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    simulation = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    created = Column(DateTime, nullable=False, index=True)
    algorithm = Column(String(50), server_default=text("''"))
    comment = Column(String(256), server_default=text("''"))
    paramjson = Column(String(2000), server_default=text("''"))


class ClusterSetup(Base):
    __tablename__ = 'cluster_setups'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(256))
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    dimensions = Column(Text, nullable=False)
    cluster = Column(Text, nullable=False)


class CrackclassificationResult(Base):
    __tablename__ = 'crackclassification_result'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    zsize = Column(INTEGER(11), nullable=False)
    samplerate = Column(INTEGER(11), nullable=False)
    position_start = Column(BIGINT(20), nullable=False)
    position_end = Column(BIGINT(20), nullable=False)
    highest_value = Column(BIGINT(20), nullable=False)
    frq_energy_list = Column(LargeBinary)


class CrackdetectionDefinition(Base):
    __tablename__ = 'crackdetection_definition'
    __table_args__ = {'comment': 'Definiert die Niveaus für Breaks und Cracks in einem Bereich'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    uniqueid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    objid = Column(INTEGER(11), nullable=False)
    objname = Column(CHAR(60), nullable=False)
    workpiece = Column(BIGINT(20), nullable=False)
    objecttype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    optionflags = Column(BIGINT(20), nullable=False, server_default=text("0"))
    channel = Column(INTEGER(11), nullable=False)
    datamode = Column(INTEGER(11), nullable=False, server_default=text("2"))
    datatype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    compression = Column(INTEGER(11), nullable=False, server_default=text("1"))
    freqcompress = Column(INTEGER(11), nullable=False, server_default=text("1"))
    auxpara1 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara2 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara3 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara4 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara5 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    framesize = Column(INTEGER(11), nullable=False)
    samplerate = Column(BIGINT(20), nullable=False)
    datarate = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    exactfrqcompr = Column(Float(asdecimal=True), nullable=False, server_default=text("1"))
    spectimens = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    freqperbandhz = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    defaultnum = Column(INTEGER(11), nullable=False, server_default=text("0"))
    setnum = Column(INTEGER(11), nullable=False)
    measuringPosition = Column(INTEGER(11), nullable=False)
    noiselevel = Column(INTEGER(11), nullable=False)
    startTriggered = Column(TINYINT(1), nullable=False)
    stopTriggered = Column(TINYINT(1), nullable=False)
    time_from = Column(BIGINT(20), nullable=False)
    time_to = Column(BIGINT(20), nullable=False)
    detectionRunActivated = Column(TINYINT(1), nullable=False)
    detectionRun = Column(BIGINT(20), nullable=False)
    frq_mask_default_value = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    delog = Column(INTEGER(11), nullable=False)
    algorithmUsed = Column(INTEGER(11), nullable=False)
    energywindow = Column(INTEGER(11), nullable=False)
    pValue = Column(INTEGER(11), nullable=False)
    pValueEnergyThreshold = Column(TINYINT(1), nullable=False)
    crack0 = Column(BIGINT(20), nullable=False)
    crack1 = Column(BIGINT(20), nullable=False)
    crack2 = Column(BIGINT(20), nullable=False)
    wdcrack0 = Column(INTEGER(11), nullable=False)
    wdcrack1 = Column(INTEGER(11), nullable=False)
    wdcrack2 = Column(INTEGER(11), nullable=False)
    crackTypesUsed = Column(INTEGER(11), nullable=False)
    showInResults = Column(TINYINT(1), nullable=False, server_default=text("1"))
    create_energy_sig = Column(TINYINT(1), nullable=False, server_default=text("0"))
    create_overview_stat = Column(TINYINT(1), nullable=False, server_default=text("0"))
    show_frqmasks_grapharea = Column(TINYINT(1), nullable=False, server_default=text("0"))
    is_disabled = Column(TINYINT(1), nullable=False, server_default=text("0"))
    sigbuf_update_ms = Column(INTEGER(11), nullable=False, server_default=text("100"))
    overviewbuf_update_ms = Column(INTEGER(11), nullable=False, server_default=text("100"))
    trigger_activated = Column(TINYINT(1), nullable=False)
    trigger_string = Column(CHAR(255), nullable=False)
    trigger_delay = Column(BIGINT(20), nullable=False)
    neg_delay = Column(BIGINT(20), nullable=False)
    json = Column(LargeBinary)
    activation_event_based = Column(TINYINT(1), nullable=False)
    ca_used = Column(TINYINT(1), nullable=False)
    ca_flank = Column(INTEGER(11), nullable=False)
    ca_flank_area = Column(INTEGER(11), nullable=False)
    ca_decay = Column(INTEGER(11), nullable=False)
    ca_broadband = Column(TINYINT(1), nullable=False)
    tri_used = Column(TINYINT(1), nullable=False)
    tri_channels = Column(INTEGER(11), nullable=False)
    cracklimit_bufname = Column(CHAR(255), nullable=False)
    cracklimitmode = Column(INTEGER(11), nullable=False, server_default=text("0"))
    bufcomppara_txt = Column(String(5000), server_default=text("''"))


class CrackdetectionFrqMask(Base):
    __tablename__ = 'crackdetection_frqMask'
    __table_args__ = (
        Index('projectid', 'projectid', 'objid', 'frq'),
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    definition_id = Column(INTEGER(11), nullable=False)
    objid = Column(INTEGER(11), nullable=False)
    type = Column(INTEGER(11), nullable=False)
    frq = Column(INTEGER(11), nullable=False)
    frqhz = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    height = Column(INTEGER(11), nullable=False)
    isnode = Column(INTEGER(11), nullable=False)
    refvalue = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    json = Column(LargeBinary)


class CrackdetectionParameter(Base):
    __tablename__ = 'crackdetection_parameter'
    __table_args__ = {'comment': 'Parameter der Risserkennung'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    signal0 = Column(INTEGER(11), nullable=False)
    disable_activation_signals = Column(TINYINT(1), nullable=False)
    filtered_energy_sig_buf = Column(TINYINT(1), nullable=False)
    emit_status_mask = Column(INTEGER(11), nullable=False)
    auto_secfft_winspread = Column(INTEGER(11), nullable=False, server_default=text("80"))
    auto_secfft_enupscale = Column(INTEGER(11), nullable=False, server_default=text("120"))
    auto_secfft_noiselevel = Column(INTEGER(11), nullable=False, server_default=text("400"))
    auto_prifft_winspread = Column(INTEGER(11), nullable=False, server_default=text("100"))
    auto_prifft_breakupscale = Column(INTEGER(11), nullable=False, server_default=text("110"))
    auto_prifft_warnupscale = Column(INTEGER(11), nullable=False, server_default=text("80"))
    auto_prifft_noiselevel = Column(INTEGER(11), nullable=False, server_default=text("400"))
    auto_secfft_loband = Column(INTEGER(11), nullable=False, server_default=text("5"))
    auto_secfft_hiband = Column(INTEGER(11), nullable=False, server_default=text("240"))
    auto_creation_runs = Column(INTEGER(11), nullable=False)
    mop_mode = Column(INTEGER(11), nullable=False)
    ioin_mapping = Column(String(100))


class CrackdetectionResult(Base):
    __tablename__ = 'crackdetection_result'
    __table_args__ = (
        Index('projectid', 'projectid', 'process'),
        {'comment': 'Fasst die Risserkennungsergebnisse fuer einen Prozess zusammen'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    simulation = Column(INTEGER(11), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    warningsviolated = Column(INTEGER(11), nullable=False)
    violationmask = Column(BIGINT(20), nullable=False)
    nodatamask = Column(BIGINT(20), nullable=False, server_default=text("0"))
    score = Column(INTEGER(11), nullable=False)
    polycyclic_set = Column(TINYINT(1), nullable=False)
    polycyclic_subprocess = Column(INTEGER(11), nullable=False)
    polycyclic_id = Column(INTEGER(11), nullable=False)
    polycyclic_num = Column(INTEGER(11), nullable=False)


class CrackdetectionResultcrack(Base):
    __tablename__ = 'crackdetection_resultcrack'
    __table_args__ = (
        Index('projectid_process', 'projectid', 'process'),
        {'comment': 'Ein als Bruch/Riss erkanntes Ereignis'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    process = Column(INTEGER(11), nullable=False, index=True)
    objid = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    simulation = Column(INTEGER(11), nullable=False)
    resultdefinitionid = Column(INTEGER(11), nullable=False)
    time = Column(BIGINT(20), nullable=False)
    time_ns = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    channel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    energy = Column(BIGINT(20), nullable=False)
    energy_pre = Column(BIGINT(20), nullable=False)
    classification = Column(INTEGER(11), nullable=False)
    diverse = Column(String(256))


class CrackdetectionResultdefinition(Base):
    __tablename__ = 'crackdetection_resultdefinition'
    __table_args__ = (
        Index('projectid', 'projectid', 'process'),
        {'comment': 'Definiert die Niveaus für Breaks und Cracks in einem Bereich'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    uniqueid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process = Column(INTEGER(11), nullable=False)
    objid = Column(INTEGER(11), nullable=False)
    simulation = Column(INTEGER(11), nullable=False)
    objname = Column(CHAR(60), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    workpiece = Column(BIGINT(20), nullable=False)
    objecttype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    optionflags = Column(BIGINT(20), nullable=False, server_default=text("0"))
    channel = Column(INTEGER(11), nullable=False)
    datamode = Column(INTEGER(11), nullable=False, server_default=text("2"))
    datatype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    compression = Column(INTEGER(11), nullable=False, server_default=text("1"))
    freqcompress = Column(INTEGER(11), nullable=False, server_default=text("1"))
    auxpara1 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara2 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara3 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara4 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    auxpara5 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    framesize = Column(INTEGER(11), nullable=False)
    samplerate = Column(BIGINT(20), nullable=False)
    datarate = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    exactfrqcompr = Column(Float(asdecimal=True), nullable=False, server_default=text("1"))
    spectimens = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    freqperbandhz = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    defaultnum = Column(INTEGER(11), nullable=False, server_default=text("0"))
    setnum = Column(INTEGER(11), nullable=False)
    measuringPosition = Column(INTEGER(11), nullable=False)
    noiselevel = Column(INTEGER(11), nullable=False)
    startTriggered = Column(TINYINT(1), nullable=False)
    stopTriggered = Column(TINYINT(1), nullable=False)
    time_from = Column(BIGINT(20), nullable=False)
    time_to = Column(BIGINT(20), nullable=False)
    detectionRunActivated = Column(TINYINT(1), nullable=False)
    detectionRun = Column(BIGINT(20), nullable=False)
    delog = Column(INTEGER(11), nullable=False)
    algorithmUsed = Column(INTEGER(11), nullable=False)
    energywindow = Column(INTEGER(11), nullable=False)
    pValue = Column(INTEGER(11), nullable=False)
    pValueEnergyThreshold = Column(TINYINT(1), nullable=False)
    tf_activated = Column(TINYINT(1), nullable=False)
    tf_movingAverageBase = Column(BIGINT(20), nullable=False)
    tf_powerThreshold = Column(BIGINT(20), nullable=False)
    tf_time = Column(TINYINT(1), nullable=False)
    crackTypesUsed = Column(INTEGER(11), nullable=False)
    showInResults = Column(TINYINT(1), nullable=False)
    create_energy_sig = Column(TINYINT(1), nullable=False, server_default=text("0"))
    create_overview_stat = Column(TINYINT(1), nullable=False, server_default=text("0"))
    sigbuf_update_ms = Column(INTEGER(11), nullable=False, server_default=text("100"))
    overviewbuf_update_ms = Column(INTEGER(11), nullable=False, server_default=text("100"))
    crack0 = Column(BIGINT(20), nullable=False)
    crack1 = Column(BIGINT(20), nullable=False)
    crack2 = Column(BIGINT(20), nullable=False)
    wdcrack0 = Column(INTEGER(11), nullable=False)
    wdcrack1 = Column(INTEGER(11), nullable=False)
    wdcrack2 = Column(INTEGER(11), nullable=False)
    warningsviolated = Column(TINYINT(1), nullable=False)
    datareceived = Column(TINYINT(1), nullable=False, server_default=text("1"))
    maxenergy = Column(BIGINT(20), nullable=False)
    maxpostenergy = Column(BIGINT(20), nullable=False)
    polycyclic_set = Column(TINYINT(1), nullable=False)
    polycyclic_subprocess = Column(INTEGER(11), nullable=False)
    polycyclic_id = Column(INTEGER(11), nullable=False)
    polycyclic_num = Column(INTEGER(11), nullable=False)
    neg_delay = Column(BIGINT(20), nullable=False)
    activation_event_based = Column(TINYINT(1), nullable=False)
    ca_used = Column(TINYINT(1), nullable=False)
    ca_flank = Column(INTEGER(11), nullable=False)
    ca_flank_area = Column(INTEGER(11), nullable=False)
    ca_decay = Column(INTEGER(11), nullable=False)
    ca_broadband = Column(TINYINT(1), nullable=False)
    tri_used = Column(TINYINT(1), nullable=False)
    tri_channels = Column(INTEGER(11), nullable=False)


class EventLog(Base):
    __tablename__ = 'event_log'
    __table_args__ = {'comment': 'Event log. Stored I/O register changes and app events'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True, server_default=text("0"))
    process = Column(INTEGER(11), nullable=False, server_default=text("0"))
    epochtimems = Column(BIGINT(20), nullable=False, server_default=text("0"))
    type = Column(INTEGER(11), nullable=False, server_default=text("0"))
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    runstate = Column(INTEGER(11), nullable=False, server_default=text("0"))
    ioin = Column(INTEGER(10), nullable=False, server_default=text("0"))
    ioout = Column(INTEGER(10), nullable=False, server_default=text("0"))
    flags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    info = Column(String(10000))


class FrqmasksNode(Base):
    __tablename__ = 'frqmasks_nodes'
    __table_args__ = {'comment': 'This table stores the node values of a frqBandMask foreign frqmasks_id references to table frqmasks.id'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    frqmasks_id = Column(INTEGER(11), nullable=False, index=True)
    frq = Column(INTEGER(11), nullable=False)
    value = Column(INTEGER(11), nullable=False)
    frqhz = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    isnode = Column(INTEGER(11), nullable=False)


class GeneralJsonResult(Base):
    __tablename__ = 'general_json_results'
    __table_args__ = {'comment': 'This table stores json objects'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    typeid = Column(INTEGER(11), nullable=False)
    creationtime = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp()"))
    variables = Column(LONGTEXT)


class HisFrqmask(Base):
    __tablename__ = 'his_frqmasks'
    __table_args__ = (
        Index('projectid', 'projectid', 'usepara'),
        {'comment': 'This table stores a history of frqBandMasks'}
    )

    id = Column(INTEGER(11), primary_key=True)
    uniqueid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    usetype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    usepara = Column(BIGINT(20), nullable=False, server_default=text("0"))
    useattr = Column(BIGINT(20), nullable=False, server_default=text("0"))
    usedata = Column(INTEGER(11), nullable=False, server_default=text("0"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    nsec = Column(BIGINT(20), nullable=False, server_default=text("0"))
    name = Column(CHAR(60), nullable=False, server_default=text("''"))
    type = Column(INTEGER(11), nullable=False, server_default=text("0"))
    frqbands = Column(INTEGER(11), nullable=False, server_default=text("512"))
    normvalue = Column(INTEGER(11), nullable=False, server_default=text("0"))
    defaultvalue = Column(INTEGER(11), nullable=False, server_default=text("0"))
    bandoffset = Column(INTEGER(11), nullable=False, server_default=text("0"))
    frqperband = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    refvalue = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    json = Column(LargeBinary)


class HumanConfirmation(Base):
    __tablename__ = 'human_confirmation'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process = Column(INTEGER(11), nullable=False)
    process_id = Column(INTEGER(11), nullable=False)
    result = Column(INTEGER(11), nullable=False, server_default=text("0"))
    comment = Column(Text, nullable=False)
    creationdate = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    score = Column(INTEGER(11), nullable=False, server_default=text("0"))
    selectionTimeHi = Column(BIGINT(20), nullable=False, server_default=text("0"))
    selectionTimeLo = Column(BIGINT(20), nullable=False, server_default=text("0"))
    selectionFrqHi = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    selectionFrqLo = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    jsoncustinfo = Column(MEDIUMTEXT)


class MachineCommunication(Base):
    __tablename__ = 'machine_communication'
    __table_args__ = {'comment': 'Tabelle stores configuration of machine communication'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    machinetype = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    machinename = Column(String(50), server_default=text("'-1'"))
    ipadress = Column(String(20), server_default=text("''"))
    port = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    isused = Column(TINYINT(1), nullable=False, server_default=text("0"))


class MachineCommunicationCommand(Base):
    __tablename__ = 'machine_communication_commands'
    __table_args__ = {'comment': 'Tabelle stores configuration of machine inputs'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    machinetype = Column(INTEGER(11), nullable=False)
    nameOfVariable = Column(String(100), server_default=text("'-'"))
    commandToMachine = Column(String(1000), server_default=text("''"))
    commandOfAnswerBeginning = Column(String(1000), server_default=text("''"))
    commandOfAnswerEnd = Column(String(1000), server_default=text("''"))


class MachineCommunicationUsed(Base):
    __tablename__ = 'machine_communication_used'
    __table_args__ = {'comment': 'Tabelle stores machine ids wanted'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    machinetype = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    IDvariable = Column(INTEGER(11), nullable=False, server_default=text("-1"))


class Maintenancelog(Base):
    __tablename__ = 'maintenancelog'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(CHAR(100), nullable=False)
    time = Column(DateTime, nullable=False)
    nextmaintenance = Column(DateTime, nullable=False)
    comment = Column(Text, nullable=False)
    version = Column(CHAR(100), nullable=False)


class MeasuringPoint(Base):
    __tablename__ = 'measuring_points'
    __table_args__ = {'comment': 'Messpunkte'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    objid = Column(INTEGER(11), nullable=False)
    port = Column(INTEGER(10), nullable=False)
    input = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    preamp = Column(INTEGER(10), nullable=False)
    filter = Column(TINYINT(1), nullable=False)
    channel = Column(INTEGER(10), nullable=False)
    cdId = Column(INTEGER(10), nullable=False)
    prId = Column(INTEGER(10), nullable=False)
    envoffset = Column(BIGINT(20), nullable=False, server_default=text("0"))


class ModbusCoilDefinition(Base):
    __tablename__ = 'modbus_coilDefinition'
    __table_args__ = {'comment': 'Modbus: Coil-Definitionen'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    address = Column(INTEGER(11), nullable=False, index=True)
    coil = Column(INTEGER(11), nullable=False)


class ModbusServerSetting(Base):
    __tablename__ = 'modbus_serverSettings'
    __table_args__ = {'comment': 'Modbus: Server-Settings'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    baud = Column(INTEGER(11), nullable=False)
    waiting = Column(INTEGER(11), nullable=False)
    outputrange = Column(INTEGER(11), nullable=False)


class MpCdResult(Base):
    __tablename__ = 'mp_cd_result'
    __table_args__ = (
        Index('projectid', 'projectid', 'process'),
        {'comment': 'MeasurePosition: Energie an Messposition'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    time = Column(DateTime, nullable=False)
    detectedmaxenergy = Column(BIGINT(20), nullable=False)
    crackdetected = Column(TINYINT(1), nullable=False)
    crackinmp = Column(INTEGER(11), nullable=False)


class MpResult(Base):
    __tablename__ = 'mp_result'
    __table_args__ = (
        Index('projectid', 'projectid', 'process'),
        {'comment': 'MeasurePosition: Ergebnisse an Position'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    measureposindex = Column(INTEGER(11), nullable=False)
    time = Column(DateTime, nullable=False)
    teachmode = Column(TINYINT(1), nullable=False)
    countindex = Column(INTEGER(11), nullable=False)
    startsample = Column(BIGINT(20), nullable=False)
    endsample = Column(BIGINT(20), nullable=False)
    detectedmaxenergy = Column(BIGINT(20), nullable=False)
    crackdetected = Column(TINYINT(1), nullable=False)
    c0 = Column(BIGINT(20), nullable=False)
    c1 = Column(BIGINT(20), nullable=False)
    c2 = Column(BIGINT(20), nullable=False)
    preamp = Column(INTEGER(11), nullable=False)
    noise = Column(INTEGER(11), nullable=False)


class OpConnectedEmitterReceiver(Base):
    __tablename__ = 'op_connected_emitter_receiver'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    emitter_id = Column(BIGINT(20), nullable=False)
    receiver_id = Column(BIGINT(20), nullable=False)


class OpConnectionPoint(Base):
    __tablename__ = 'op_connection_point'

    id = Column(INTEGER(11), primary_key=True)
    connection_id = Column(INTEGER(11), nullable=False)
    idx = Column(INTEGER(11), nullable=False)
    point_x = Column(Float(asdecimal=True), nullable=False)
    point_y = Column(Float(asdecimal=True), nullable=False)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))


class OpConnection(Base):
    __tablename__ = 'op_connections'

    id = Column(INTEGER(11), primary_key=True)
    conn1_id = Column(INTEGER(11), nullable=False, index=True)
    conn2_id = Column(INTEGER(11), nullable=False, index=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    pipeline = Column(TINYINT(1), nullable=False, server_default=text("0"))
    buff_size = Column(INTEGER(11), nullable=False, server_default=text("1"))


class OpConnectorEmitterReceiver(Base):
    __tablename__ = 'op_connector_emitter_receiver'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    pos_x = Column(Float(asdecimal=True), nullable=False)
    pos_y = Column(Float(asdecimal=True), nullable=False)


class OpConnector(Base):
    __tablename__ = 'op_connectors'

    id = Column(INTEGER(11), primary_key=True)
    operator_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    in_out_state = Column(INTEGER(11), nullable=False)
    index_pos = Column(INTEGER(11), nullable=False)
    contype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    type = Column(String(256), server_default=text("''"))
    name = Column(String(256), server_default=text("''"))
    shortText = Column(String(50), server_default=text("''"))


class OpOperatorBase(Base):
    __tablename__ = 'op_operator_bases'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    op_type = Column(String(256), server_default=text("''"))
    pos_x = Column(Float(asdecimal=True), nullable=False)
    pos_y = Column(Float(asdecimal=True), nullable=False)
    enabled = Column(TINYINT(1), nullable=False)
    parent_custom_op_id = Column(INTEGER(11), nullable=False)
    propagate_param_widget = Column(TINYINT(1), nullable=False)


class OpOperatorDefaultConfig(Base):
    __tablename__ = 'op_operator_default_configs'

    id = Column(INTEGER(11), primary_key=True)
    operator_type = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    config = Column(MEDIUMBLOB, nullable=False)
    is_init_default = Column(TINYINT(1), nullable=False)


class OpOperatorUserDefined(Base):
    __tablename__ = 'op_operator_user_defined'

    id = Column(INTEGER(11), primary_key=True)
    dbversion = Column(INTEGER(11), nullable=False, server_default=text("0"))
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    name = Column(Text, nullable=False)
    istemplate = Column(TINYINT(1), nullable=False, server_default=text("0"))


class OpOperator(Base):
    __tablename__ = 'op_operators'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    specialization_json = Column(MEDIUMBLOB, nullable=False)


class OpResult(Base):
    __tablename__ = 'op_result'
    __table_args__ = {'comment': 'This table stores different floating point values generated by operators'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    process = Column(INTEGER(11), nullable=False, index=True)
    operator = Column(INTEGER(11), nullable=False)
    issimulated = Column(INTEGER(11), nullable=False, index=True)
    datatype = Column(String(16), index=True, server_default=text("''"))
    tag = Column(String(16), index=True, server_default=text("''"))
    x = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    y = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    z = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))


class OpTreeStructure(Base):
    __tablename__ = 'op_tree_structure'

    id = Column(INTEGER(11), primary_key=True)
    parent_id = Column(INTEGER(11), nullable=False)
    dbversion = Column(INTEGER(11), nullable=False, server_default=text("0"))
    model_id = Column(Text, nullable=False)
    projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    pos_in_list = Column(INTEGER(11), nullable=False)
    name = Column(String(256), server_default=text("''"))
    is_leaf = Column(INTEGER(11), nullable=False)
    leaf_db_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))


class PatternBase(Base):
    __tablename__ = 'pattern_base'

    pb_id = Column(INTEGER(11), primary_key=True)
    pb_created_pattern_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    pb_created_pattern_uuid = Column(CHAR(38), nullable=False, index=True, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    pb_created_pattern_name = Column(String(256))
    pb_creation_timestamp = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    pb_result_id = Column(INTEGER(11), nullable=False, index=True, server_default=text("-1"))
    pb_result_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    pb_refobj_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    pb_refobj_uuid = Column(CHAR(38), nullable=False, index=True, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    pb_refobj_name = Column(Text, nullable=False)
    pb_used_tag = Column(String(100), server_default=text("''"))
    pb_simulated = Column(INTEGER(11), nullable=False, server_default=text("0"))


class PatternResultobj(Base):
    __tablename__ = 'pattern_resultobjs'
    __table_args__ = (
        Index('projectid_process', 'projectid', 'process'),
        Index('projectid_process_issimulated', 'projectid', 'process', 'issimulated'),
        {'comment': 'Pattern recognition table with search results'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(ForeignKey('projects.projectid'), nullable=False, index=True)
    process = Column(ForeignKey('process.process'), nullable=False, index=True)
    confignumber = Column(INTEGER(11), nullable=False, server_default=text("1"))
    measureposindex = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    measurepostime = Column(BIGINT(20), nullable=False, server_default=text("0"))
    measureposcounter = Column(INTEGER(11), nullable=False)
    determinebuffer_id = Column(BIGINT(20), nullable=False, server_default=text("0"))
    groupid = Column(INTEGER(11))
    version = Column(INTEGER(11), nullable=False, server_default=text("0"))
    comparingmethod = Column(INTEGER(11), nullable=False)
    resultflags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    refobjprimalid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    pattern_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    issimilar = Column(TINYINT(1), nullable=False, server_default=text("0"))
    issimulated = Column(INTEGER(11), nullable=False, index=True, server_default=text("0"))
    triggered = Column(TINYINT(1), nullable=False, server_default=text("0"))
    neverprocessinfo = Column(TINYINT(1), nullable=False, server_default=text("0"))
    channel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    tstart = Column(BIGINT(20), nullable=False, server_default=text("0"))
    tend = Column(BIGINT(20), nullable=False, server_default=text("0"))
    frqbegin = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    frqend = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    significance_tstart = Column(BIGINT(20), nullable=False, server_default=text("0"))
    significance_tend = Column(BIGINT(20), nullable=False, server_default=text("0"))
    scale_amplitude = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    scale_time = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    time_offset = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    similarity = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    similarity_scaled = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    date = Column(DateTime, nullable=False)
    energysum = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    linear_energysum = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    average = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    linear_average = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    standarddeviation = Column(Float(asdecimal=True), nullable=False)
    maxamplitude = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    maxrefamplitude = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    maxenergyspec = Column(BIGINT(20), nullable=False)
    foundspec = Column(BIGINT(20), nullable=False, server_default=text("0"))
    foundspecreal = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    referenceobjectid = Column(INTEGER(11), nullable=False, index=True, server_default=text("-1"))
    score = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    scoreabsolute = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    locked_at = Column(BIGINT(20), nullable=False)
    misc01 = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    misc02 = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    usemultiplyscaling = Column(TINYINT(1), nullable=False)
    usedelogforscaling = Column(TINYINT(1), nullable=False)
    energyref = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    paramjson = Column(JSON, nullable=False, server_default=text("''"))
    foreigndbid = Column(INTEGER(11), nullable=False, index=True, server_default=text("0"))
    foreignrelationtype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    idtag = Column(String(100), index=True, server_default=text("''"))
    originbufferid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    clusterid = Column(INTEGER(11), nullable=False, server_default=text("0"))
    clustered_result_count = Column(INTEGER(11), nullable=False, server_default=text("0"))

    _process = relationship('Process', back_populates = '_pattern_result_objects')
    project = relationship('Project', back_populates = 'pattern_result_objects')

    @property
    def related_process(self):
        for process in self.project.processes:
            if process.process == self.process:
                return process
        return None 


class PatternResultobjsFilterSetting(Base):
    __tablename__ = 'pattern_resultobjs_filter_settings'
    __table_args__ = {'comment': 'Stores filter options for pattern result objects graphs'}

    id = Column(INTEGER(11), primary_key=True)
    name = Column(CHAR(255), nullable=False)
    date = Column(DateTime, nullable=False)
    simulationNo = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    channel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    triggered = Column(TINYINT(1), nullable=False, server_default=text("0"))
    idTag = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    measurePosition = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    energySumFrom = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    energySumTo = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    similarityFrom = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    similarityTo = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    timePosFrom = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    timePosTo = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    signalLengthFrom = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    signalLengthTo = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    dateTimeFrom = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    dateTimeTo = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    refObjPrimalId = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    useFilterChannel = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterTriggered = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterIdTag = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterMP = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterEnergy = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterSimilarity = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterSignalLength = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterTimePos = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterCreationTime = Column(TINYINT(1), nullable=False, server_default=text("0"))
    useFilterPattern = Column(TINYINT(1), nullable=False, server_default=text("0"))
    signalLengthMult = Column(INTEGER(11), nullable=False, server_default=text("0"))
    timePosMult = Column(INTEGER(11), nullable=False, server_default=text("0"))


class PatternSubresultobj(Base):
    __tablename__ = 'pattern_subresultobjs'
    __table_args__ = {'comment': 'Pattern recognition table with search subresults'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    resultid = Column(BIGINT(20), nullable=False)
    time_ns = Column(BIGINT(20), nullable=False)
    score = Column(BIGINT(20), nullable=False)


class ProcessAreaMarker(Base):
    __tablename__ = 'process_area_marker'
    __table_args__ = {'comment': 'Tabelle fuer alle Markierungen im Prozess -> Area'}

    id = Column(INTEGER(11), primary_key=True)
    process_id = Column(INTEGER(11), nullable=False, index=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    type = Column(TINYINT(3), nullable=False, index=True)
    area = Column(TINYINT(4), nullable=False)
    channel = Column(INTEGER(11), nullable=False)
    start_s = Column(BIGINT(20), nullable=False)
    end_s = Column(BIGINT(20), nullable=False)
    start_frq = Column(INTEGER(11), nullable=False)
    end_frq = Column(INTEGER(11), nullable=False)
    starthz = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    endhz = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    start_t = Column(BIGINT(20), nullable=False)
    end_t = Column(BIGINT(20), nullable=False)
    flags = Column(INTEGER(11), nullable=False)
    flag_height = Column(INTEGER(11), nullable=False)
    comment = Column(String(1024))


class ProcessArea(Base):
    __tablename__ = 'process_areas'
    __table_args__ = (
        Index('process_id', 'process_id', 'area', 'timeset'),
        {'comment': 'Tabelle fuer alle Zeitinformationen -> Process -> Project  (in Abhaengigkeit vom Projekt)'}
    )

    id = Column(INTEGER(11), primary_key=True)
    process_id = Column(INTEGER(11), nullable=False)
    area = Column(TINYINT(3), nullable=False)
    timeset = Column(TINYINT(3), nullable=False)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    timeset_comment = Column(String(128))
    main_buffer_id = Column(BIGINT(20), nullable=False)
    start_time = Column(BIGINT(20), nullable=False)
    range_time = Column(BIGINT(20), nullable=False)
    start_time_store = Column(BIGINT(20), nullable=False)
    range_time_store = Column(BIGINT(20), nullable=False)
    pre_datamode = Column(INTEGER(11), nullable=False)
    pre_datatype = Column(INTEGER(11), nullable=False)
    pre_datakind = Column(INTEGER(11), nullable=False)
    pre_compress = Column(INTEGER(11), nullable=False)
    pre_channel = Column(INTEGER(11), nullable=False)
    ref_layer_stored = Column(TINYINT(1), nullable=False)
    helplayer_offset = Column(INTEGER(11), nullable=False)
    yscale_offset = Column(INTEGER(11), nullable=False)
    gfx_y_scale = Column(INTEGER(11), nullable=False)
    colorscale = Column(INTEGER(11), nullable=False)
    prefbuffer = Column(String(512), server_default=text("''"))
    json = Column(LargeBinary)


class ProcessBuffer(Base):
    __tablename__ = 'process_buffer'
    __table_args__ = {'comment': 'Tabelle fuer alle Buffer -> Process -> Project'}

    id = Column(INTEGER(11), primary_key=True)
    process_id = Column(INTEGER(11), nullable=False, index=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    pool_file_id = Column(BIGINT(20), nullable=False, index=True, server_default=text("0"))
    buffer_id = Column(BIGINT(20), nullable=False, server_default=text("0"))
    date_creation = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp()"))
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("'0000-00-00 00:00:00'"))
    measuretime_ms = Column(BIGINT(20), nullable=False, server_default=text("0"))
    partition_uuid = Column(CHAR(38), nullable=False, index=True, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    extid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    deletelockflag = Column(INTEGER(11), nullable=False, server_default=text("0"))
    path = Column(String(1024), index=True)
    comment = Column(String(4096))
    duration = Column(BIGINT(20), nullable=False)
    sizebytes = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    datamode = Column(INTEGER(11), nullable=False)
    datatype = Column(INTEGER(11), nullable=False)
    datakind = Column(INTEGER(11), nullable=False)
    dataflags = Column(INTEGER(11), nullable=False)
    channel = Column(INTEGER(11), nullable=False)
    compress = Column(INTEGER(11), nullable=False)
    fcompress = Column(INTEGER(11), nullable=False, server_default=text("1"))
    auxpara0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    auxpara1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    auxpara2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    auxpara3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    auxpara4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    auxpara5 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    simmode = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    skip_samples = Column(BIGINT(20), nullable=False)
    skip_time = Column(BIGINT(20), nullable=False)
    trunc_samples = Column(BIGINT(20), nullable=False)
    trunc_time = Column(BIGINT(20), nullable=False)
    skip_lofrq = Column(INTEGER(11), nullable=False)
    trunc_hifrq = Column(INTEGER(11), nullable=False)
    buffer_idx = Column(TINYINT(3), nullable=False, server_default=text("0"))
    process = Column(INTEGER(11), nullable=False, index=True, server_default=text("-1"))
    processrange = Column(INTEGER(11), nullable=False, server_default=text("1"))
    subprocess = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    polycyclic_part = Column(TINYINT(1), nullable=False)
    polycyclic_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    polycyclic_num = Column(INTEGER(11), nullable=False)
    modusagemask = Column(BIGINT(20), nullable=False, server_default=text("0"))
    datafilever = Column(INTEGER(11), nullable=False, server_default=text("0"))
    bytespersample = Column(INTEGER(11), nullable=False, server_default=text("0"))
    samplesperframe = Column(INTEGER(11), nullable=False, server_default=text("0"))
    adctype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    adcbitres = Column(INTEGER(11), nullable=False, server_default=text("0"))
    samplefreq = Column(INTEGER(11), nullable=False, server_default=text("0"))
    interpolated = Column(TINYINT(1), nullable=False, server_default=text("0"))
    bufcomppara_txt = Column(String(10000), server_default=text("''"))
    transformations_txt = Column(String(5000), server_default=text("''"))
    islikelymeasure = Column(TINYINT(1), nullable=False, server_default=text("1"))
    measurerestarted = Column(TINYINT(1), nullable=False, server_default=text("0"))
    flags = Column(INTEGER(11), nullable=False, server_default=text("0"))


class ProcessBufferZaxesinfo(Base):
    __tablename__ = 'process_buffer_zaxesinfo'
    __table_args__ = {'comment': 'Tabelle fuer Z-Axes information for buffer'}

    id = Column(INTEGER(11), primary_key=True)
    process_buffer_id = Column(INTEGER(11), nullable=False, index=True)
    process_id = Column(INTEGER(11), nullable=False, index=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    idx = Column(INTEGER(11), nullable=False, index=True)
    colno = Column(INTEGER(11), nullable=False)
    color = Column(INTEGER(11), nullable=False)
    zpos = Column(INTEGER(11), nullable=False)
    scale = Column(Float(asdecimal=True), nullable=False)
    min = Column(Float(asdecimal=True), nullable=False)
    max = Column(Float(asdecimal=True), nullable=False)
    offset = Column(Float(asdecimal=True), nullable=False)
    headtext = Column(String(256))


class ProcessDecisionResult(Base):
    __tablename__ = 'process_decision_results'
    __table_args__ = (
        Index('projectid', 'projectid', 'process', 'simulation'),
        {'comment': 'Fasst die Resultate von Entscheidungsregeln fuer einen Prozess zusammen'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    simulation = Column(INTEGER(11), nullable=False, server_default=text("0"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    label = Column(INTEGER(11), nullable=False, server_default=text("0"))
    score = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    comment = Column(Text, nullable=False)


class ProcessMarker(Base):
    __tablename__ = 'process_marker'
    __table_args__ = {'comment': 'Tabelle fuer alle Markierungen im Prozess -> Process -> Project'}

    id = Column(INTEGER(11), primary_key=True)
    process_id = Column(INTEGER(11), nullable=False, index=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    type = Column(TINYINT(3), nullable=False, index=True, server_default=text("0"))
    comment = Column(String(1024), server_default=text("''"))
    channel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    start_s = Column(BIGINT(20), nullable=False, server_default=text("0"))
    end_s = Column(BIGINT(20), nullable=False, server_default=text("0"))
    start_frq = Column(INTEGER(11), nullable=False, server_default=text("0"))
    end_frq = Column(INTEGER(11), nullable=False, server_default=text("0"))
    startns = Column(BIGINT(20), nullable=False, server_default=text("0"))
    endns = Column(BIGINT(20), nullable=False, server_default=text("0"))
    starthz = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    endhz = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    timevalid = Column(TINYINT(1), nullable=False, server_default=text("0"))
    freqvalid = Column(TINYINT(1), nullable=False, server_default=text("0"))


class ProjectJsonModelTable(Base):
    __tablename__ = 'project_json_model_table'
    __table_args__ = {'comment': 'This table stores json objects for jsontablemodel data'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    creationtime = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp()"))
    name = Column(Text, nullable=False)
    jsondata = Column(LONGTEXT)


class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = {'comment': 'Tabelle speichert alle Projekt / Werkstuecktyp Informationen'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, unique=True)
    shared_projectid_opnet = Column(BIGINT(20), nullable=False, server_default=text("0"))
    locked = Column(TINYINT(1), nullable=False)
    no_auto_buffer_delete = Column(TINYINT(1), nullable=False)
    project_version = Column(INTEGER(11), nullable=False)
    analyzer_version = Column(String(20))
    helpid = Column(INTEGER(11), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    date_db_creation = Column(DateTime, nullable=False)
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    project_name = Column(String(256))
    project_name_prefix = Column(String(256))
    project_file_directory = Column(String(1024))
    project_file_host = Column(String(1024))
    project_flags = Column(BIGINT(20), nullable=False, server_default=text("0"))
    user_creation = Column(String(128))
    user_level_creation = Column(INTEGER(11), nullable=False, server_default=text("0"))
    workpiece_selection = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    comment = Column(String(4096), server_default=text("''"))
    raw_datadir_0 = Column(String(1024))
    raw_datadir_1 = Column(String(1024))
    raw_datadir_2 = Column(String(1024))
    raw_datadir_3 = Column(String(1024))
    raw_datadir_x = Column(String(1024), server_default=text("''"))
    buffer_datadir_0 = Column(String(1024))
    buffer_datadir_1 = Column(String(1024))
    buffer_datadir_2 = Column(String(1024))
    buffer_datadir_3 = Column(String(1024))
    buffer_datadir_x = Column(String(1024), server_default=text("''"))
    base_dir = Column(String(1024))
    sshbase_dir = Column(String(1024), nullable=False, server_default=text("''"))
    processinfo_dir = Column(String(1024))
    measure_multipath = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_record_io = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_record_trigger = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_automation_enable = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_trigger_enable = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_pre_sensor_test = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_post_sensor_test = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_pre_send_preamp = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_post_send_preamp = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_monitor_dbhold = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_disable_nav_monitor = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_disable_nav_measure = Column(TINYINT(1), nullable=False, server_default=text("0"))
    measure_monitor_channel = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_osc_channel = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_process_limit = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_raw_data_limit = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_compr_data_limit = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_raw_data_keep_every = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_compr_data_keep_every = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_raw_data_limit_ext = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_compr_data_limit_ext = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_raw_data_keep_every_ext = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_compr_data_keep_every_ext = Column(INTEGER(11), nullable=False, server_default=text("0"))
    measure_skip_z_display_val = Column(INTEGER(11), nullable=False, server_default=text("0"))
    pulse_port = Column(INTEGER(11), nullable=False, server_default=text("0"))
    pulse_gain = Column(INTEGER(11), nullable=False, server_default=text("0"))
    pulse_count = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_monitor_enable = Column(TINYINT(1), nullable=False, server_default=text("0"))
    energy_monitor_channel = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_energy_threshold = Column(BIGINT(20), nullable=False, server_default=text("0"))
    energy_warn_min_amplitude = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_spects = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_loband = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_hiband = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_setting_no = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_datatype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    energy_warn_buffer_compr = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_count = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_current = Column(INTEGER(11), nullable=False, server_default=text("0"))
    polycyclic_count = Column(INTEGER(11), nullable=False, server_default=text("0"))
    polycyclic_current = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_first_raw_undeleted = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_first_compr_undeleted = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_first_valid = Column(INTEGER(11), nullable=False, server_default=text("0"))
    process_ref_process_time = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_diskspace = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_diskspace_0 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_diskspace_1 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_diskspace_2 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_diskspace_3 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    process_last_process_time = Column(BIGINT(20), nullable=False, server_default=text("0"))
    polycyclic_mode = Column(TINYINT(1), nullable=False, server_default=text("0"))
    gui_mem = Column(TINYINT(1), nullable=False, server_default=text("0"))
    guisettingsflags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    guisettings_file = Column(String(1024), server_default=text("''"))
    guisettings_ext = Column(LONGTEXT)
    refobj_usertype_set = Column(String(256), server_default=text("''"))

    pattern_result_objects = relationship('PatternResultobj', back_populates = 'project')
    process_events = relationship('ProcessEvent', back_populates = 'project')
    part_numbers = relationship('ProjectsPartnumber', back_populates = 'project')
    processes = relationship('Process', back_populates = 'project')


class ProjectsAppvar(Base):
    __tablename__ = 'projects_appvar'
    __table_args__ = (
        Index('projectid_varname', 'projectid', 'varname'),
        {'comment': 'Tabelle stores values of static and global appvars'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    varname = Column(String(100), server_default=text("''"))
    varvalue = Column(String(10000), server_default=text("''"))
    vartype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))


class ProjectsArea(Base):
    __tablename__ = 'projects_areas'
    __table_args__ = (
        Index('projectid', 'projectid', 'area'),
        {'comment': 'Tables contains view the configuration for areas'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    area = Column(INTEGER(11), nullable=False)
    wishdatamode = Column(INTEGER(11), nullable=False)
    wishdatatype = Column(INTEGER(11), nullable=False)
    wishcompress = Column(INTEGER(11), nullable=False)
    wishchannel = Column(INTEGER(11), nullable=False)
    colorscale = Column(INTEGER(11), nullable=False)
    gfxyscale = Column(INTEGER(11), nullable=False)
    frozen = Column(INTEGER(11), nullable=False)
    infoboxflags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    wishfingerprint = Column(String(512), server_default=text("''"))
    json = Column(LargeBinary)


class ProjectsChannel(Base):
    __tablename__ = 'projects_channel'
    __table_args__ = (
        Index('projectid', 'projectid', 'channel'),
        {'comment': 'Tabelle mit den Kanal Einstellungen  (in Abhaengigkeit vom Projekt)'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    channel = Column(INTEGER(11), nullable=False)
    port = Column(INTEGER(11), nullable=False)
    record_fft = Column(TINYINT(1), nullable=False)
    record_sig = Column(TINYINT(1), nullable=False)
    record_adtype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    samplerateshift = Column(INTEGER(11), nullable=False)
    fft_oversample = Column(INTEGER(11), nullable=False)
    fft_window_func = Column(INTEGER(11), nullable=False)
    fft_logvalue = Column(INTEGER(11), nullable=False, server_default=text("12"))
    obj_trigger_bit = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    fftbytespersample = Column(INTEGER(11), nullable=False)
    fftnormampl = Column(INTEGER(11), nullable=False)
    fftadbitres = Column(INTEGER(11), nullable=False)
    sigbytespersample = Column(INTEGER(11), nullable=False)
    signormampl = Column(INTEGER(11), nullable=False)
    sigadbitres = Column(INTEGER(11), nullable=False)
    virt_inputstream = Column(INTEGER(11), nullable=False, server_default=text("0"))


class ProjectsFrqmask(Base):
    __tablename__ = 'projects_frqmasks'
    __table_args__ = (
        Index('projectid', 'projectid', 'type'),
        {'comment': 'This table stores project related frqBandMask'}
    )

    id = Column(INTEGER(11), primary_key=True)
    uniqueid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    projectid = Column(BIGINT(20), nullable=False)
    usetype = Column(INTEGER(11), nullable=False, server_default=text("2"))
    type = Column(INTEGER(11), nullable=False)
    my_id = Column(INTEGER(10), nullable=False)
    my_name = Column(CHAR(60), nullable=False)
    internal_comment = Column(CHAR(30), nullable=False, server_default=text("''"))
    foreignid = Column(INTEGER(11), nullable=False, server_default=text("0"))
    frq_bands = Column(INTEGER(11), nullable=False)
    norm_value = Column(INTEGER(11), nullable=False)
    default_value = Column(INTEGER(11), nullable=False)
    bandoffset = Column(INTEGER(11), nullable=False, server_default=text("0"))
    frqperband = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    refvalue = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    json = Column(LargeBinary)


class ProjectsMux(Base):
    __tablename__ = 'projects_mux'
    __table_args__ = (
        Index('projectid', 'projectid', 'muxport'),
        {'comment': 'Tabelle mit den Einstellungen der Multiplexer(ports) (in Abhaengigkeit vom Projekt)'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    muxport = Column(INTEGER(11), nullable=False)
    preamp_multimask = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    power_state = Column(TINYINT(1), nullable=False)
    filter_state = Column(TINYINT(1), nullable=False)
    greenled_state = Column(TINYINT(1), nullable=False)
    redled_state = Column(TINYINT(1), nullable=False)
    gain = Column(INTEGER(11), nullable=False)
    status = Column(INTEGER(11), nullable=False)


class ProjectsPartnumber(Base):
    __tablename__ = 'projects_partnumber'

    id = Column(INTEGER(11), primary_key=True)
    partnumber = Column(String(128), unique=True)
    projectidgroup = Column(ForeignKey('projects.projectid'), nullable=False)
    partdescription = Column(String(1024), server_default=text("''"))
    partuuid = Column(CHAR(38), nullable=False, index=True, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    project = relationship('Project', back_populates = 'part_numbers')
    processes = relationship('Process', back_populates = 'part_number')


class ProjectsSelection(Base):
    __tablename__ = 'projects_selections'
    __table_args__ = (
        Index('projectid', 'projectid', 'setting', 'mark'),
        {'comment': 'Tabelle mit den abgespeicherten Selection Sets  (in Abhaengigkeit vom Projekt)'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    setting = Column(INTEGER(11), nullable=False)
    mark = Column(INTEGER(11), nullable=False)
    mark_string = Column(String(20000))


class ProjectsTrigger(Base):
    __tablename__ = 'projects_trigger'
    __table_args__ = {'comment': 'Tabelle mit den Triggern der Projekte'}

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    number = Column(INTEGER(11), nullable=False)
    trigger_string = Column(String(20000), server_default=text("''"))


class ProjectsVar(Base):
    __tablename__ = 'projects_var'
    __table_args__ = {'comment': 'Tabelle speichert zusaetzliche variable Werte wie Enumerator'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    projects_partnumber_id = Column(INTEGER(11))
    enum0 = Column(INTEGER(11), nullable=False)
    enum1 = Column(INTEGER(11), nullable=False)
    enum2 = Column(INTEGER(11), nullable=False)
    enum3 = Column(INTEGER(11), nullable=False)
    enum4 = Column(INTEGER(11), nullable=False)
    enum0name = Column(CHAR(25), nullable=False)
    enum1name = Column(CHAR(25), nullable=False)
    enum2name = Column(CHAR(25), nullable=False)
    enum3name = Column(CHAR(25), nullable=False)
    enum4name = Column(CHAR(25), nullable=False)
    enum0max = Column(INTEGER(11), nullable=False)
    enum1max = Column(INTEGER(11), nullable=False)
    enum2max = Column(INTEGER(11), nullable=False)
    enum3max = Column(INTEGER(11), nullable=False)
    enum4max = Column(INTEGER(11), nullable=False)
    enum0idscale = Column(CHAR(100), nullable=False)
    enum1idscale = Column(CHAR(100), nullable=False)
    enum2idscale = Column(CHAR(100), nullable=False)
    enum3idscale = Column(CHAR(100), nullable=False)
    enum4idscale = Column(CHAR(100), nullable=False)
    process_cnt = Column(INTEGER(11), nullable=False)
    process_sub_cnt = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    process_polycyclic_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    process_polycyclic_cnt = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    process_pending_sub_process = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    process_pending_comment = Column(CHAR(200), nullable=False)
    process_pending_serial = Column(CHAR(200), nullable=False)


class ProjectsVirtdev(Base):
    __tablename__ = 'projects_virtdev'
    __table_args__ = {'comment': 'Tabelle stores configuration of virtual input and output devices'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    virtdevconfig = Column(String(4096), server_default=text("''"))


class Qas(Base):
    __tablename__ = 'qass'

    id = Column(INTEGER(11), primary_key=True)
    key_name = Column(CHAR(100), nullable=False, unique=True)
    key_value = Column(String(100), server_default=text("''"))


class QassBackuphistory(Base):
    __tablename__ = 'qass_backuphistory'
    __table_args__ = {'comment': 'History of system backups with backup filenames and dates'}

    id = Column(INTEGER(11), primary_key=True)
    date_created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    date_removed = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    filepath = Column(String(512))
    backupflags = Column(INTEGER(11), nullable=False)
    removed = Column(TINYINT(1), nullable=False, server_default=text("0"))
    ishistory = Column(TINYINT(1), nullable=False, server_default=text("0"))


class RefobjUsertype(Base):
    __tablename__ = 'refobj_usertypes'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(256))
    setname = Column(String(256))


class Refobj(Base):
    __tablename__ = 'refobjs'

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    db_tableversion = Column(INTEGER(11), nullable=False)
    confignumber = Column(INTEGER(11), nullable=False, server_default=text("1"))
    pos_indatalist = Column(INTEGER(11), nullable=False)
    type = Column(INTEGER(11), nullable=False, server_default=text("0"))
    usertype = Column(String(256), server_default=text("''"))
    name = Column(Text, nullable=False)
    flags = Column(INTEGER(11), nullable=False, server_default=text("1"))
    primalid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    primal_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    pattern_buffer_path = Column(String(1024))
    mask_buffer_path = Column(String(1024))
    pattern_buffer_id = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mask_buffer_id = Column(BIGINT(20), nullable=False, server_default=text("0"))
    extra_buffer_id = Column(BIGINT(20), nullable=False, server_default=text("0"))
    noisethreshold = Column(BIGINT(20), nullable=False, server_default=text("0"))
    screenshotpath = Column(Text, nullable=False)
    sourcebufferpath = Column(Text, nullable=False)
    frqbandbegin = Column(INTEGER(11), nullable=False)
    frqbandend = Column(INTEGER(11), nullable=False)
    frq_hz_begin = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    frq_hz_end = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    frq_per_band = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    specbegin = Column(BIGINT(20), nullable=False)
    specend = Column(BIGINT(20), nullable=False)
    timebegin = Column(BIGINT(20), nullable=False)
    timeend = Column(BIGINT(20), nullable=False)
    spec_duration = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    origin_frqbandbegin = Column(INTEGER(11), nullable=False, server_default=text("0"))
    origin_frqbandend = Column(INTEGER(11), nullable=False, server_default=text("0"))
    origin_frq_hz_begin = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    origin_frq_hz_end = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    origin_frq_per_band = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    origin_specbegin = Column(BIGINT(20), nullable=False, server_default=text("0"))
    origin_specend = Column(BIGINT(20), nullable=False, server_default=text("0"))
    origin_timebegin = Column(BIGINT(20), nullable=False, server_default=text("0"))
    origin_timeend = Column(BIGINT(20), nullable=False, server_default=text("0"))
    origin_spec_duration = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    sourcebuffercompressratio = Column(BIGINT(20), nullable=False)
    sourcebufferdatamode = Column(BIGINT(20), nullable=False)
    sourcebufferdatarate = Column(BIGINT(20), nullable=False)
    sourcebuffertype = Column(BIGINT(20), nullable=False)
    sourcebufferfrequencybands = Column(INTEGER(11), nullable=False)
    paramjson = Column(String(2000), server_default=text("''"))
    pattern_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    common_pattern_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    common_pattern_similarity = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    common_pattern_amplitude_scaling = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    common_pattern_time_scaling = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    pattern_base_count = Column(INTEGER(11), nullable=False, server_default=text("1"))
    based_on_patterns = Column(LONGTEXT, nullable=False, server_default=text("''"))
    based_on_projectid = Column(BIGINT(20), nullable=False, server_default=text("0"))
    based_on_process = Column(INTEGER(11), nullable=False, server_default=text("0"))
    comment = Column(String(1000), server_default=text("''"))
    detecting_operator = Column(String(256), server_default=text("''"))
    detecting_operator_parameters = Column(String(5000), server_default=text("''"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))
    creating_system = Column(String(1024), server_default=text("''"))
    tag = Column(String(100), server_default=text("''"))
    energy = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    linear_energy = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))


class ResultRelation(Base):
    __tablename__ = 'result_relations'
    __table_args__ = {'comment': 'similarity relations between results'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False, index=True)
    from_resultid = Column(BIGINT(20), nullable=False, index=True)
    to_resultid = Column(BIGINT(20), nullable=False, index=True)
    similarity = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    linear_similarity = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    scale_amplitude = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    scale_time = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    date = Column(DateTime, nullable=False, index=True)
    groupid = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    clustering_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))


class StatcolldataR(Base):
    __tablename__ = 'statcolldata_r'

    id = Column(INTEGER(11), primary_key=True)
    date_creation = Column(DateTime, nullable=False)
    setid = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    sample = Column(BIGINT(20), nullable=False)
    v0 = Column(Float(asdecimal=True))


class StatcolldataRr(Base):
    __tablename__ = 'statcolldata_rr'

    id = Column(INTEGER(11), primary_key=True)
    date_creation = Column(DateTime, nullable=False)
    setid = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    sample = Column(BIGINT(20), nullable=False)
    v0 = Column(Float(asdecimal=True))
    v1 = Column(Float(asdecimal=True))


class Statcollection(Base):
    __tablename__ = 'statcollections'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(CHAR(100), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    handle = Column(BIGINT(20), nullable=False)
    boundto = Column(INTEGER(11), nullable=False)
    datatype = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    activeset = Column(INTEGER(11), nullable=False)


class Statcollset(Base):
    __tablename__ = 'statcollset'

    id = Column(INTEGER(11), primary_key=True)
    date_creation = Column(DateTime, nullable=False)
    collid = Column(INTEGER(11), nullable=False)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)


class TriggerLog(Base):
    __tablename__ = 'trigger_log'
    __table_args__ = (
        Index('projectid', 'projectid', 'process'),
        {'comment': 'Speichert ausgeslöste Trigger'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(BIGINT(20), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    timestamp = Column(INTEGER(11), nullable=False)
    processtimestamp = Column(INTEGER(11), nullable=False)
    trg_type = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    trg_para = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    trg_attr = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    cmd = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    cmd_para = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    cmd_attr = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    cmd_delay = Column(INTEGER(11), nullable=False, server_default=text("-1"))


class VsetMeasureConfig(Base):
    __tablename__ = 'vset_MeasureConfig'
    __table_args__ = (
        Index('vset_projectid', 'vset_projectid', 'vset_index'),
        {'comment': 'This VarSet holds MeasureConfig settings'}
    )

    id = Column(INTEGER(11), primary_key=True)
    vset_projectid = Column(BIGINT(20), nullable=False)
    vset_index = Column(INTEGER(11), nullable=False)
    vset_date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    mcMonitorChannel = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorBufCompPara = Column(String(512), server_default=text("''"))
    mcMonitorFPSArea = Column(INTEGER(11), nullable=False, server_default=text("10"))
    mcMonitorRangeMsArea = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcMonitorChannelArea2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorBufCompParaArea2 = Column(String(512), server_default=text("''"))
    mcMonitorFPSArea2 = Column(INTEGER(11), nullable=False, server_default=text("10"))
    mcMonitorRangeMsArea2 = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcMonitorChannelArea3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorBufCompParaArea3 = Column(String(512), server_default=text("''"))
    mcMonitorFPSArea3 = Column(INTEGER(11), nullable=False, server_default=text("10"))
    mcMonitorRangeMsArea3 = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcMonitorChannelArea4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorBufCompParaArea4 = Column(String(512), server_default=text("''"))
    mcMonitorFPSArea4 = Column(INTEGER(11), nullable=False, server_default=text("10"))
    mcMonitorRangeMsArea4 = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcMonitorChannelArea5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorBufCompParaArea5 = Column(String(512), server_default=text("''"))
    mcMonitorFPSArea5 = Column(INTEGER(11), nullable=False, server_default=text("10"))
    mcMonitorRangeMsArea5 = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcFrequencyBands = Column(INTEGER(11), nullable=False, server_default=text("512"))
    mcMultiPath = Column(TINYINT(1), nullable=False)
    mcRecordIo = Column(TINYINT(1), nullable=False)
    mcMonitorEnergy = Column(TINYINT(1), nullable=False)
    mcMarkTrigger = Column(TINYINT(1), nullable=False)
    mcTriggerEnabled = Column(TINYINT(1), nullable=False)
    mcModbusEnabled = Column(TINYINT(1), nullable=False)
    mcAnalyzeFrqBands = Column(TINYINT(1), nullable=False)
    mcDisableNavOnMeasure = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcDisableNavOnMonitor = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcAutomationEnabled = Column(TINYINT(1), nullable=False)
    mcUseObjTriggerBits = Column(TINYINT(1), nullable=False)
    mcPreMeasureSensorTest = Column(TINYINT(1), nullable=False)
    mcPreMeasureSendPreamp = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcPostMeasureSensorTest = Column(TINYINT(1), nullable=False)
    mcPostMeasureSendPreamp = Column(TINYINT(1), nullable=False)
    mcWriteMeasureData = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcForceOptiDevRegWrite = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcEarlyStartFeedback = Column(TINYINT(1), nullable=False)
    mcMeasureOptionFlags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcPostMeasureFlags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMonitorHistorySizeMs = Column(INTEGER(11), nullable=False, server_default=text("3000"))
    mcMeasureStartSyncDelayMs = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcMeasuringSkipZDisplayVal = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mc24bitConverterOnChannel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcSetupViewMp = Column(TINYINT(1), nullable=False)
    mcProcessLimit = Column(INTEGER(11), nullable=False, server_default=text("100000"))
    mcRawDataLimit = Column(INTEGER(11), nullable=False, server_default=text("100"))
    mcComprDataLimit = Column(INTEGER(11), nullable=False, server_default=text("1000"))
    mcRawDataKeepEvery = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcComprDataKeepEvery = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcRawDataLimitExt = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcComprDataLimitExt = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcRawDataKeepEveryExt = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcComprDataKeepEveryExt = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcVirtualInDataLimit = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufCompressType0 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor0 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor0 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude0 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample0 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf0 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask0 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString0 = Column(String(512), server_default=text("''"))
    mcBufDescription0 = Column(String(512), server_default=text("''"))
    mcbufCompressType1 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor1 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor1 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude1 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample1 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf1 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask1 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString1 = Column(String(512), server_default=text("''"))
    mcBufDescription1 = Column(String(512), server_default=text("''"))
    mcbufCompressType2 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor2 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor2 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude2 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample2 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf2 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask2 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString2 = Column(String(512), server_default=text("''"))
    mcBufDescription2 = Column(String(512), server_default=text("''"))
    mcbufCompressType3 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor3 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor3 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude3 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample3 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf3 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf3 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask3 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString3 = Column(String(512), server_default=text("''"))
    mcBufDescription3 = Column(String(512), server_default=text("''"))
    mcbufCompressType4 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor4 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor4 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude4 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample4 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf4 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf4 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask4 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString4 = Column(String(512), server_default=text("''"))
    mcBufDescription4 = Column(String(512), server_default=text("''"))
    mcbufCompressType5 = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    mcbufCompressFactor5 = Column(INTEGER(11), nullable=False, server_default=text("32"))
    mcbufFrqCompressFactor5 = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcbufAppliedMasks5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufIncomingMasks5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufEmbeddedMask5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcbufNormAmplitude5 = Column(BIGINT(20), nullable=False, server_default=text("16384"))
    mcBytesPerSample5 = Column(INTEGER(11), nullable=False, server_default=text("2"))
    mcAuxPara0buf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara1buf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara2buf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara3buf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara4buf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcAuxPara5buf5 = Column(BIGINT(20), nullable=False, server_default=text("0"))
    mcResampleFlagsBuf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcNestingModeBuf5 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcTargetChannelMask5 = Column(BIGINT(20), nullable=False, server_default=text("15"))
    mcBufSettingString5 = Column(String(512), server_default=text("''"))
    mcBufDescription5 = Column(String(512), server_default=text("''"))
    mcSignalMaximumCompression = Column(TINYINT(1), nullable=False, server_default=text("1"))
    mcSignalMaximumComprMask = Column(INTEGER(11), nullable=False, server_default=text("15"))
    mcPulseTestConnectedPort = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcPulseTestStrength = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcPulseTestCount = Column(INTEGER(11), nullable=False, server_default=text("1"))
    mcSignalMaximumComprFac0 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcSignalMaximumComprFac1 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcSignalMaximumComprFac2 = Column(INTEGER(11), nullable=False, server_default=text("0"))
    mcSignalMaximumComprFac3 = Column(INTEGER(11), nullable=False, server_default=text("0"))


class VsetPrSearchConfig(Base):
    __tablename__ = 'vset_PrSearchConfig'
    __table_args__ = (
        Index('vset_projectid', 'vset_projectid', 'vset_index'),
        {'comment': 'This VarSet holds the configuration for pattern recognition search and visualization settings'}
    )

    id = Column(INTEGER(11), primary_key=True)
    vset_projectid = Column(BIGINT(20), nullable=False)
    vset_index = Column(INTEGER(11), nullable=False)
    vset_date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    prShowFoundRefObjects = Column(TINYINT(1), nullable=False)
    prShowNonFitting = Column(TINYINT(1), nullable=False)
    prShowFoundRefObjOnlyIfSelected = Column(TINYINT(1), nullable=False)
    prShowFoundRefObjPickBoxes = Column(TINYINT(1), nullable=False, server_default=text("1"))
    prShowFoundRefObjInfoPanels = Column(TINYINT(1), nullable=False, server_default=text("1"))
    prShowPickBoxAsFrame = Column(TINYINT(1), nullable=False)
    prShowNoiseInRefObjs = Column(TINYINT(1), nullable=False)
    prActivateOpencl = Column(TINYINT(1), nullable=False)
    prAmplitudeScaleFactorsForCreatingTestBuffer = Column(String(512), server_default=text("''"))
    prTimeScaleFactorsForCreatingTestBuffer = Column(String(512), server_default=text("''"))
    prShowResultTree = Column(TINYINT(1), nullable=False)
    prEnableResultTree = Column(TINYINT(1), nullable=False)
    prShowPatternVectors = Column(TINYINT(1), nullable=False)
    prPinMonitors = Column(String(512), server_default=text("''"))
    prShowResultFilterForce = Column(String(512), server_default=text("''"))
    prShowResultFilterHide = Column(String(512), server_default=text("''"))


class VsetSimulationBufferConfig(Base):
    __tablename__ = 'vset_SimulationBufferConfig'
    __table_args__ = (
        Index('vset_projectid', 'vset_projectid', 'vset_index'),
        {'comment': 'This VarSet holds configuration for simulation buffers'}
    )

    id = Column(INTEGER(11), primary_key=True)
    vset_projectid = Column(BIGINT(20), nullable=False)
    vset_index = Column(INTEGER(11), nullable=False)
    vset_date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    SimEnabled = Column(TINYINT(1), nullable=False)
    SimChan1Enabled = Column(TINYINT(1), nullable=False)
    SimChan1BufPath = Column(String(512), server_default=text("''"))
    SimChan1Flags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    SimChan2Enabled = Column(TINYINT(1), nullable=False)
    SimChan2BufPath = Column(String(512), server_default=text("''"))
    SimChan2Flags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    SimChan3Enabled = Column(TINYINT(1), nullable=False)
    SimChan3BufPath = Column(String(512), server_default=text("''"))
    SimChan3Flags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    SimChan4Enabled = Column(TINYINT(1), nullable=False)
    SimChan4BufPath = Column(String(512), server_default=text("''"))
    SimChan4Flags = Column(INTEGER(11), nullable=False, server_default=text("0"))
    SetSimulatedIOInRegFromChannel = Column(INTEGER(11), nullable=False, server_default=text("-1"))


class VsetGlobal(Base):
    __tablename__ = 'vset_global'
    __table_args__ = (
        Index('class_type', 'class_type', 'idx', 'key_name'),
    )

    id = Column(INTEGER(11), primary_key=True)
    class_type = Column(INTEGER(11), nullable=False)
    idx = Column(INTEGER(11), nullable=False)
    class_name = Column(CHAR(100), nullable=False)
    key_name = Column(CHAR(100), nullable=False)
    key_value = Column(String(1024))


class ExtWorkpieceType(Base):
    __tablename__ = 'ext_workpiece_type'
    __table_args__ = {'comment': 'This table stores is part of a table collection for complex measurement settings. This table holds the attributes of a workpiece type (e.g. geometry).'}

    id = Column(INTEGER(10), primary_key=True)
    projectid = Column(ForeignKey('projects.projectid', ondelete='CASCADE'), nullable=False, index=True)
    date_created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    name = Column(Text)
    description = Column(Text)
    json_entry = Column(Text)
    json_entry_extended = Column(LONGTEXT)
    curr_setting_id = Column(INTEGER(11))

    project = relationship('Project')


class HisFrqmasksNode(Base):
    __tablename__ = 'his_frqmasks_nodes'
    __table_args__ = {'comment': 'This table stores the node values of a frqBandMask foreign his_frqmasks_id references to table frqmasks.id'}

    id = Column(INTEGER(11), primary_key=True)
    his_frqmasks_id = Column(ForeignKey('his_frqmasks.id', ondelete='CASCADE'), nullable=False, index=True)
    frq = Column(INTEGER(11), nullable=False)
    value = Column(INTEGER(11), nullable=False)
    frqhz = Column(Float(asdecimal=True), nullable=False, server_default=text("-1"))
    isnode = Column(INTEGER(11), nullable=False)

    his_frqmasks = relationship('HisFrqmask')


class Process(Base):
    __tablename__ = 'process'
    __table_args__ = (
        Index('projectid_process_date', 'projectid', 'process', 'date_creation'),
        Index('projectid_process', 'projectid', 'process'),
        {'comment': 'Anker Tabelle fuer alle Prozessinformationen  (in Abhaengigkeit vom Projekt)'}
    )

    id = Column(INTEGER(11), primary_key=True)
    projects_id = Column(INTEGER(11), nullable=False)
    projectid = Column(ForeignKey('projects.projectid'), nullable=False, index=True)
    process = Column(INTEGER(11), nullable=False, index=True)
    sub_process = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    projects_partnumber_foreign_id = Column(ForeignKey('projects_partnumber.id'), index=True)
    date_creation = Column(DateTime, nullable=False, index=True, server_default=text("'2001-01-01 00:00:00'"))
    date_modified = Column(TIMESTAMP, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))
    measuretime_ms = Column(BIGINT(20), nullable=False, server_default=text("0"))
    db_version = Column(INTEGER(11), nullable=False)
    polyprocess = Column(INTEGER(11), nullable=False)
    duration = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    files = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    hidden = Column(TINYINT(1), nullable=False)
    comment = Column(String(4096))
    scancode = Column(String(256))
    serial = Column(String(256))
    infotext = Column(String(1024), server_default=text("''"))
    jsoncustinfo = Column(MEDIUMTEXT)
    timeset = Column(INTEGER(11), nullable=False)
    do_not_delete = Column(TINYINT(1), nullable=False)
    measurerestarted = Column(TINYINT(1), nullable=False, server_default=text("0"))
    enum0 = Column(INTEGER(11), nullable=False)
    enum1 = Column(INTEGER(11), nullable=False)
    enum2 = Column(INTEGER(11), nullable=False)
    enum3 = Column(INTEGER(11), nullable=False)
    enum4 = Column(INTEGER(11), nullable=False)
    raw_deleted = Column(TINYINT(1), nullable=False)
    compr_deleted = Column(TINYINT(1), nullable=False)
    raw_del_time = Column(DateTime, nullable=False)
    compr_del_time = Column(DateTime, nullable=False)
    legend_offset_time = Column(BIGINT(20), nullable=False)
    legend_offset_flag = Column(TINYINT(4), nullable=False)
    skip_time = Column(BIGINT(20), nullable=False)
    trunc_time = Column(BIGINT(20), nullable=False)
    skip_lofrq = Column(INTEGER(11), nullable=False)
    trunc_hifrq = Column(INTEGER(11), nullable=False)
    polycyclic_part = Column(TINYINT(1), nullable=False)
    polycyclic_id = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    video_offsettime = Column(BIGINT(20), nullable=False, server_default=text("-1"))
    external_locked_video = Column(String(1024))

    part_number = relationship('ProjectsPartnumber', back_populates = 'processes')
    _pattern_result_objects = relationship('PatternResultobj', back_populates = '_process')
    process_events = relationship('ProcessEvent', back_populates = 'related_process')
    project = relationship('Project', back_populates = 'processes')

    @property
    def pattern_result_objects(self):
        return [pattern_result_obj for pattern_result_obj in self._pattern_result_objects if pattern_result_obj.projectid == self.projectid]

class ProcessBufferPath(Base):
    __tablename__ = 'process_buffer_path'

    id = Column(INTEGER(11), primary_key=True)
    process_buffer_foreign_id = Column(ForeignKey('process_buffer.id', ondelete='CASCADE'), nullable=False, index=True)
    filetype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    filepath = Column(String(1024), server_default=text("''"))

    process_buffer_foreign = relationship('ProcessBuffer')


class ProjectsDoc(Base):
    __tablename__ = 'projects_docs'
    __table_args__ = {'comment': 'Table contains misc project related documentation texts. Identified by doctype'}

    id = Column(INTEGER(11), primary_key=True)
    projects_foreign_id = Column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    doctype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    subtype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    doctext = Column(LONGTEXT)

    projects_foreign = relationship('Project')


class ProjectsDynchannel(Base):
    __tablename__ = 'projects_dynchannel'
    __table_args__ = {'comment': 'Tabelle stores input dynamic channel configuration for project'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(ForeignKey('projects.projectid', ondelete='CASCADE'), nullable=False, index=True)
    channel = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    inputtype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    muxport = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    virtualport = Column(INTEGER(11), nullable=False, server_default=text("-1"))
    inputstream = Column(INTEGER(11), nullable=False, server_default=text("0"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("0"))
    channelconfig = Column(String(4096), server_default=text("''"))

    project = relationship('Project')


class ProjectsFile(Base):
    __tablename__ = 'projects_files'

    id = Column(INTEGER(11), primary_key=True)
    projects_foreign_id = Column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    filetype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    subtype = Column(INTEGER(11), nullable=False, server_default=text("0"))
    filepath = Column(String(1024), server_default=text("''"))
    partition_uuid = Column(CHAR(38), nullable=False, server_default=text("'{00000000-0000-0000-0000-000000000000}'"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))

    projects_foreign = relationship('Project')


class ProjectsMiscdatum(Base):
    __tablename__ = 'projects_miscdata'
    __table_args__ = {'comment': 'Tabelle stores configuration of virtual input and output devices'}

    id = Column(INTEGER(11), primary_key=True)
    projectid = Column(ForeignKey('projects.projectid', ondelete='CASCADE'), nullable=False, index=True)
    datatype = Column(INTEGER(11), nullable=False, index=True, server_default=text("0"))
    data = Column(String(20000), server_default=text("''"))
    date_creation = Column(DateTime, nullable=False, server_default=text("'2001-01-01 00:00:00'"))

    project = relationship('Project')


class ExtMeasurementSetting(Base):
    __tablename__ = 'ext_measurement_settings'
    __table_args__ = {'comment': 'This table stores is part of a table collection for complex measurement settings. This table holds specific measurement parameters.'}

    id = Column(INTEGER(10), primary_key=True)
    workpiece_type_id = Column(ForeignKey('ext_workpiece_type.id'), index=True)
    date_created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    name = Column(Text)
    description = Column(Text)
    json_entry = Column(Text)
    json_entry_extended = Column(LONGTEXT)

    workpiece_type = relationship('ExtWorkpieceType')


class ProcessEvent(Base):
    __tablename__ = 'process_events'
    __table_args__ = (
        Index('projectid_timestamp', 'projectid', 'timestamp'),
        Index('projectid_process', 'projectid', 'process'),
        {'comment': 'stores process related events'}
    )

    id = Column(INTEGER(11), primary_key=True)
    process_events_foreign_id = Column(ForeignKey('process.id', ondelete='CASCADE'), nullable=False, index=True)
    projectid = Column(ForeignKey('projects.projectid'), nullable=False)
    process = Column(INTEGER(11), nullable=False)
    date = Column(DATETIME(fsp=3), nullable=False, server_default=text("'2001-01-01 00:00:00.000'"))
    timestamp = Column(BIGINT(20), nullable=False)
    processtimestamp = Column(BIGINT(20), nullable=False)
    eventcountid = Column(BIGINT(20), nullable=False)
    eventtype = Column(String(512), server_default=text("''"))
    eventdata = Column(MEDIUMTEXT)

    related_process = relationship('Process', back_populates = 'process_events')
    project = relationship('Project', back_populates = 'process_events')


class ExtMeasurementSery(Base):
    __tablename__ = 'ext_measurement_series'
    __table_args__ = {'comment': 'This table stores is part of a table collection for complex measurement settings. This table holds information about a series of measurements over different workpieces.'}

    id = Column(BIGINT(20), primary_key=True)
    workpiece_type_id = Column(ForeignKey('ext_workpiece_type.id'), index=True)
    settings_id = Column(ForeignKey('ext_measurement_settings.id'), index=True)
    date_created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    name = Column(Text)
    description = Column(Text)
    json_entry = Column(Text)
    json_entry_extended = Column(LONGTEXT)

    settings = relationship('ExtMeasurementSetting')
    workpiece_type = relationship('ExtWorkpieceType')


class ExtWorkpiece(Base):
    __tablename__ = 'ext_workpiece'
    __table_args__ = {'comment': 'This table stores is part of a table collection for complex measurement settings. This table represents particular workpieces.'}

    id = Column(BIGINT(20), primary_key=True)
    measurement_series_id = Column(ForeignKey('ext_measurement_series.id'), index=True)
    workpiece_idx = Column(INTEGER(11))
    name = Column(Text)
    description = Column(Text)
    json_entry = Column(Text)
    json_entry_extended = Column(LONGTEXT)

    measurement_series = relationship('ExtMeasurementSery')


class ExtMeasurement(Base):
    __tablename__ = 'ext_measurement'
    __table_args__ = {'comment': 'This table stores is part of a table collection for complex measurement settings. This table holds information about a single measurement at a single point of a workpiece.'}

    id = Column(BIGINT(20), primary_key=True)
    workpiece_id = Column(ForeignKey('ext_workpiece.id', ondelete='CASCADE'), index=True)
    date_created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    process = Column(INTEGER(11), index=True)
    result_id = Column(BIGINT(20))
    pos_idx = Column(INTEGER(11))
    repetition = Column(INTEGER(11))
    simulation = Column(INTEGER(11))
    json_entry = Column(Text)
    json_entry_extended = Column(LONGTEXT)

    workpiece = relationship('ExtWorkpiece')
