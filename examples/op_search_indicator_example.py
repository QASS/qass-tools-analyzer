from qass.tools.analyzer import search_indicator

si = search_indicator.SearchIndicator(rti, si_out, label='MyTest')


def eval_process_init():
    stream = stream_in.readInputValue()
    si.process_init(stream)


def eval_process_run():
    si.tick()
