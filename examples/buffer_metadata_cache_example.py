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
from qass.tools.analyzer.buffer_metadata_cache import BufferMetadataCache, BufferMetadata
from qass.tools.analyzer import buffer_parser as bp



def main():
    # create an instance of the cache
    cache = BufferMetadataCache(BufferMetadataCache.create_session(), bp.Buffer)
    # syncing is only needed once. Resyncing new files is still a lot faster than opening every buffer file
    # deleted files are not yet removed from the database
    cache.synchronize_directory("/directory/to/sync/") # replace with your path

    # search for matching metadata
    # create a metadata object with the properties you want the results to match
    buffer_metadata = BufferMetadata(frq_bands = 512, channel = 1, compression_time = 4, datatype = bp.Buffer.DATATYPE.COMP_AVERAGE)
    # query the cache using the metadata object
    matching_files = cache.get_matching_files(buffer_metadata = buffer_metadata) # returns a list of complete filepaths as strings

    # Returns all buffer filepaths with channel = 1, A frequency compression of 4, 
    # processes above 100 sorted by the process number
    files = cache.get_matching_files(
                    buffer_metadata = BufferMetadata(channel = 1, compression_frq = 4),
                    filter_function = lambda bm: bm.process > 100,
                    sort_key = lambda bm: bm.process)

    # Returns all buffer objects with channel = 1, A frequency compression of 4, 
    # processes above 100 sorted by the process number
    buffers = cache.get_matching_buffers(
                    buffer_metadata = BufferMetadata(channel = 1, compression_frq = 4),
                    filter_function = lambda bm: bm.process > 100,
                    sort_key = lambda bm: bm.process)

    # providing a filter function
    # the following is equivalent to the above query that uses the BufferMetadata object
    # provide a custom function that returns a conjunction of attributes (return true when the buffer file should be included in the results)
    matching_files = cache.get_matching_files(filter_function = lambda buffer_metadata: buffer_metadata.frq_bands == 512 and buffer_metadata.channel == 1 and buffer_metadata.compression_time == 4 and buffer_metadata.datatype = bp.Buffer.DATATYPE.COMP_AVERAGE)



if __name__ == "__main__":
    main()
