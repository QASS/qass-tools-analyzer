from typing import Callable
import warnings
from PySide2.QtCore import QObject, Signal, Slot, Qt, SIGNAL, QThread
from PySide2.QtGui import QGuiApplication

try:
    from Analyzer.OutputRedirect import OutputRedirect_Manager
    import Analyzer.Debugger
except:
    warnings.warn("Analyzer modules couldn't be imported, are you inside the Analyzer environment?", RuntimeWarning)


__all__ = ["inMainThread"]

class inMainThread(QObject):
    def __init__(self, synchron=True):
        super().__init__()
        self.synchron = synchron
        # move self QObject to the main thread
        main_thread = QGuiApplication.instance().thread()
        self.moveToThread(main_thread)

    called = Signal()
    
    def __call__(self, method: Callable):
        """
        Invokes a method on the main thread. Taking care of garbage collection "bugs".
        """
        def inner_func(*args, **kwargs):
            if QThread.currentThread() == QGuiApplication.instance().thread():
                return method(*args, **kwargs)
            
            self._method = method
            
            # do not garbage collect this self object until the function has finished.
            self.setParent(QGuiApplication.instance())
            
            self.params = args
            self.kwargs = kwargs
            
            self.stdout_redirector = OutputRedirect_Manager.getInstance().getCurrentOutRedirect()
            self.stderr_redirector = OutputRedirect_Manager.getInstance().getCurrentErrRedirect()
            self.debuggers = Analyzer.Debugger.DebuggerManager.getInstance().getCurrDebuggers()
            
            if self.synchron:
                # This function must not be called from the main thread - this would result in a deadlock
                QObject.disconnect(self, SIGNAL('called()'), self.execute)
                self.called.connect(self.execute, Qt.BlockingQueuedConnection)
                self.called.emit()
                # the result will only be available in the synchronous execution mode

                if self._exc_info is not None:
                    type, exc, traceback = self._exc_info
                    raise exc
                return self._result
            else:
                QObject.disconnect(self, SIGNAL('called()'), self.execute)
                self.called.connect(self.execute)
                self.called.emit()
        
        return inner_func

    @Slot()
    def execute(self):
        OutputRedirect_Manager.getInstance().registerStdOutHandler(self.stdout_redirector)
        OutputRedirect_Manager.getInstance().registerStdErrHandler(self.stderr_redirector)
        
        for dbg in self.debuggers:
            Analyzer.Debugger.DebuggerManager.getInstance().registerDebugger(dbg)
        
        self._result = None
        self._exc_info = None
        
        try:
            # actually execute the wrapped method
            self._result = self._method(*self.params, **self.kwargs)
        except Exception as e:
            import sys
            self._exception = e
            self._exc_info = sys.exc_info()
        finally:
            for dbg in self.debuggers:
                Analyzer.Debugger.DebuggerManager.getInstance().unregisterDebugger(dbg)

            OutputRedirect_Manager.getInstance().unregisterStdOutHandler(self.stdout_redirector)
            OutputRedirect_Manager.getInstance().unregisterStdErrHandler(self.stderr_redirector)
            # decref self -> trigger garbage collector
            self.setParent(None)
