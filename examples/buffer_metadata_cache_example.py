from qass_tools.analyzer import BufferMetadataCache
from qass_tools.analytic import buffer_parser as bp



def main():
    # create an instance of the cache
    cache = BufferMetadataCache(BufferMetadataCache.create_session(), bp.buffer)
    # syncing is only needed once. Resyncing new files is still a lot faster than opening every buffer file
    # deleted files are not yet removed from the database
    cache.synchronize_directory("/directory/to/sync/") # replace with your path

    # search for matching metadata
    # create a metadata object with the properties you want the results to match
    buffer_metadata = BufferMetadataCache.BufferMetadata(frq_bands = 512, channel = 1, compression_time = 4)
    # query the cache using the metadata object
    matching_files = cache.get_matching_files(buffer_metadata = buffer_metadata) # returns a list of complete filepaths as strings

    # providing a filter function
    # the following is equivalent to the above query that uses the BufferMetadata object
    # provide a custom function that returns a conjunction of attributes (return true when the buffer file should be included in the results)
    matching_files = cache.get_matching_files(filter_function = lambda buffer_metadata: buffer_metadata.frq_bands == 512 and buffer_metadata.channel == 1 and buffer_metadata.compression_time == 4)



if __name__ == "__main__":
    main()