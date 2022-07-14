buff_path = '/data1/MyProject/raw2/MyProject_00008p71840c1b02_dump_00.000'

import qass_tools.analyzer.buffer_parser as bp

with bp.Buffer(buff_file) as buff:
    column_list = ['times', 'spectrums', 'inputs']
    meta_info = buff.block_infos(columns = column_list, changes_only=True)
    # ---- Here you already got the meta info. Below is just an example what you can do with it.
    
    
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
    

