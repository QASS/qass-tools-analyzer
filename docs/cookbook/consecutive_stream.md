The [`ConsecutiveStream`][qass.tools.analyzer.consecutive_stream] class is an abstraction over multiple [`Buffer`][qass.tools.analyzer.buffer_parser] objects that represent consecutive measurements. If you are not familiar with the [`Buffer`][qass.tools.analyzer.buffer_parser] class check out the [`Buffer Parser Cookbook`](./buffer_parser.md) entries first.


## Create from a collection

A [`ConsecutiveStream`][qass.tools.analyzer.consecutive_stream] class can be used as a static collection of [`Buffer`][qass.tools.analyzer.buffer_parser] objects in which case it abstracts the local indices from the individual data streams away and treats all streams as one large data stream.

```py
from qass.tools.analyzer.buffer_parser import Buffer
from qass.tools.analyzer.buffer_metadata_cache import BufferMetadataCache, BufferMetadata, select
from qass.tools.analyzer.consecutive_stream import ConsecutiveStream

cache = BufferMetadataCache()
cache.synchronize_directory("my_project")
streams = (
        cache.get_matching_buffers(select(BufferMetadata)
            .filter_by(channel=1, compression_time=4)
            .order_by(BufferMetadata.process.asc()))
            )
con_stream = ConsecutiveStream(max_streams=len(streams))
con_stream.add_streams(streams)
```

The created [`ConsecutiveStream`][qass.tools.analyzer.consecutive_stream] should now have the cumulated amount of samples of all the input streams so the check

```py
assert con_stream.spec_count == sum([s.spec_count for s in streams])
```

should pass.

!!! warning
    The [`ConsecutiveStream.spec_count`][qass.tools.analyzer.consecutive_stream.ConsecutiveStream.spec_count] property is just a convenience property and does not necessarily return the amount of samples that is available. Use [`ConsecutiveStream.min_sample_idx`][qass.tools.analyzer.consecutive_stream.ConsecutiveStream.min_sample_idx] and [`ConsecutiveStream.max_sample_idx`][qass.tools.analyzer.consecutive_stream.ConsecutiveStream.max_sample_idx] to verify the available samples in the stream that you use for calls to [`ConsecutiveStream.get_data`][qass.tools.analyzer.consecutive_stream.ConsecutiveStream.get_data].

Now we could just fetch all the available data in consecutive stream (make sure you have enough RAM to do that).

```py
data = con_stream.get_data(con_stream.min_sample_idx, con_stream.max_sample_idx)
data.shape
```

## Use as a FIFO stream buffer

The [`ConsecutiveStream`][qass.tools.analyzer.consecutive_stream] internally uses a FIFO buffer to keep track of internal data streams. Sometimes it is expensive to keep data stream objects around for too long which is why you might only want to hold a couple for accessing recent data and discard the oldest stream once a new one is created. This can be achieved by using the `max_streams` parameter during the creation. The parameter defines the size of the internal FIFO buffer. Once the buffer is full, adding a new data stream will lead to the oldest one being evicted.


```py
from qass.tools.analyzer.buffer_parser import Buffer
from qass.tools.analyzer.consecutive_stream import ConsecutiveStream

files = [...] # stream file paths

con_stream = ConsecutiveStream(max_streams=3)

for file in files:
    start_idx = con_stream.add_stream(Buffer(file))
    # ... do stuff
```

In this example the consecutive stream only holds a maximum of three data streams at any given time. This also means that it is not possible to retrieve the complete range of $[0, \text{spec_count}]$ in every iteration because older streams are already evicted. Only the range $[\text{min_sample_idx}, \text{max_sample_idx}]$ is available in every iteration.
