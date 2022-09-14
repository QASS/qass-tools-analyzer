from Analyzer.Core import Buffer_Py_IF

from qass_tools.analyzer.input_observer import InputObserver

def my_callback(input_config, start, end):
    """print every change
    
    :param input_config: The tuple with (byte, bit, state, delay)
    :param start: start time of the range in nanoseconds
    :param end: end time of the range in nanoseconds
    """
    print(input_config, start / 1e6, end / 1e6)

# observes the first byte and first bit
input_observer = InputObserver(rti, [(1, 1, True, 0)], my_callback)



def eval_process_init():
    
    fft_stream = STREAM_IN.readInputValue()
    input_observer.process_init(fft_stream)    
    
def eval_run():
    input_observer.tick(rti.getCurrentTime())
    
def eval_process_end():
    input_observer.process_end()
