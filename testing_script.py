from qass.tools.analyzer.buffer_metadata_cache import Buffer
import sys
print(sys.executable)
print(sys.version)




BUFFER = "/data1/Federnwinden-B/buffer1/Federnwinden-B_00026p0159c0b02"
# BUFFER = "/data1/Federnwinden-B/raw1/Federnwinden-B_00026p0159c0b01_dump_00.000"

with Buffer(BUFFER) as buff:
    # column_list = ['times', 'spectrums', 'inputs']
    column_list = ['times', 'spectrums', 'inputs', 'outputs', 'preamp_gain', 'mux_port', 'measure_positions']
    meta_info = buff.block_infos(columns = column_list, changes_only=True)
    # ---- Here you already got the meta info. Below is just an example what you can do with it.
    print(f"meta_info: {meta_info}")
    
    #here you can filter for example you could check for a certain io values
    io_should_be = 5
    for i, mi in enumerate(meta_info):
        if mi[2] == io_should_be:
            # the start spec is in the second column of this row:
            start_idx = mi[1]
            # the end spec is in the first column of the next row:
            end_idx = meta_info[i+1, 1]
            
            data = buff.get_data(start_idx, end_idx)
            #do something with the data in this region

# with Buffer(BUFFER) as buf:

#     data = buf.get_data()
#     print(f"This is the data: {data}")
#     print(f"This is the data slice: {data[0,0:64]}")
#     print(f"This is the data.shape: {data.shape}")
#     print(f"This is the analyzer_version: {buf.analyzer_version}")
#     print(f"This is the compression_time: {buf.compression_time}")
#     print(f"This is the compression_frq: {buf.compression_frq}")
#     print(f"This is the avg_time: {buf.avg_time}")
#     print(f"This is the avg_frq: {buf.avg_frq}")
#     print(f"This is the bit_resolution: {buf.bit_resolution}")