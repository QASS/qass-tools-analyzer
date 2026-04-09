# Qass Tools Analyzer

**Library of tools to work with the Analyzer4D software or data produced by it.**


Load a data stream file from the Analyzer4D software using the [`Buffer`](api/buffer_parser.md) class:

```py
from qass.tools.analyzer.buffer_parser import Buffer

my_file = "file"
with Buffer(my_file) as stream:
    print(stream.process)
```


Organize your data files from the Analyzer4D software and make them searchable using the [`BufferMetadataCache`](api/buffer_metadata_cache.md):

```py
from qass.tools.analyzer.buffer_metadata_cache import (
    BufferMetadataCache,
    BufferMetadata,
    select
    )

project_dir = "project_dir"
cache = BufferMetadataCache()
cache.synchronize_directory(project_dir)
files = cache.get_matching_files(select(BufferMetadata).filter_by(process=42))
```
