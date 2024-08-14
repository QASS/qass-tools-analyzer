<!--
Copyright (c) 2022 QASS GmbH.
Website: https://qass.net
Contact: QASS GmbH <info@qass.net>

This file is part of Qass tools 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
-->
# Analyzer package for Qass Tools

This package contains python modules that can be used to interact with the [Analyzer4D](https://business.qass.net/en/software) software or with the data it produces.

It provides:

- A parser for the files containing the measurement data by the [Analyzer4D](https://business.qass.net/en/software)
- An index to query for measurement data
- A database abstraction for the [Analyzer4D](https://business.qass.net/en/software)
- Abstractions for modules available in the operator network of the [Analyzer4D](https://business.qass.net/en/software)

Check out the **[documentation](https://qass.github.io/qass-tools-analyzer/)**!

## Examples

**Read Buffer files**

In the example we provide the path to a buffer file to the Buffer class and use the with-statement to open it to read the process number.

```py
from qass.tools.analyzer.buffer_parser import Buffer

buffer_file = "path/to/my/buffer_file"
with Buffer(buffer_file) as buff:
   print(buff.process)
   data = buff.get_data() # this is a numpy array
```

**Query Buffer files**

In this example we create an instance of the cache and synchronize it with the directory `my/directory`. 
We then create a template BufferMetadata object and use it with the cache to query for all buffers with a compression_frq = 8. 
You can use all properties that are in `BufferMetadata.properties`. The `BufferMetadataCache.get_matching_buffers()` method 
returns a list of Buffer objects that are in this case sorted by their process number (as specified in the sort_key).

```py
from qass.tools.analyzer.buffer_metadata_cache import BufferMetadataCache as BMC, BufferMetadata as BM, select

cache = BMC()
cache.synchronize_directory("my/directory")

results = cache.get_matching_buffers(query=select(BM).filter(BM.compression_frq==8).order_by(BM.process))
```

