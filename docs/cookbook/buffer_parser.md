## Loading Analyzer4D data files

Load a data stream file from the Analyzer4D software using the [`Buffer`](buffer_parser.md) class:

```py
from qass.tools.analyzer.buffer_parser import Buffer

my_file = "file"
with Buffer(my_file) as stream:
    print(stream.process)
```


## Plotting the spectrogram with `datamode=DATAMODE_FFT`


```py
import matplotlib.pyplot as plt

from qass.tools.analyzer.buffer_parser import Buffer

my_file = "file"
with Buffer(my_file) as stream:
    assert stream.datamode = Buffer.DATAMODE.DATAMODE_FFT, "Not a spectrogram"
    data = stream.get_data()

fig, ax = plt.subplots()
ax.imshow(data.T, aspect="auto", origin="lower")
plt.show()
```


## Truncate frequency domain of data stream file `datamode=DATAMODE_FFT`

In this example we assume that the spectrogram has an upper frequency of 800kHz. We truncate the data by such that only the data in the range of 100 - 700kHz remains. Truncating essentially means applying a high-pass and a low-pass filter.


```py
import matplotlib.pyplot as plt

from qass.tools.analyzer.buffer_parser import Buffer

START_FRQ_KHZ = 100
END_FRQ_KHZ = 700

my_file = "file"
with Buffer(my_file) as stream:
    assert stream.datamode = Buffer.DATAMODE.DATAMODE_FFT, "Not a spectrogram"
    data = stream.get_data()

HIGH_PASS = int(START_FRQ_KHZ * 1000 / stream.frq_per_band)
LOW_PASS = int(END_FRQ_KHZ * 1000 / stream.frq_per_band)

trunc_data = data[:, HIGH_PASS: LOW_PASS]

fig, ax = plt.subplots()
ax.imshow(data.T, aspect="auto", origin="lower")
plt.show()
```
