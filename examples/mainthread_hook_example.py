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
'''
This is an example for the usage of the mainthread_hook.inMainThread decorator.
This decorator can be used to execute a function in the main thread although the executing thread is not the main thread.
The decorator is based on Qt's EventLoop mechanism.
It can only work inside a Qt Application.
'''

from qass.tools.mainthread_hook import inMainThread

@inMainThread(synchron=True)
def func(testA, testB):
    import matplotlib.pyplot as plt
    plt.plot(testA, testB)
    # It seems as if the Qt matplotlib backend ignores the block=True statement.
    plt.show(block=True)

@inMainThread()
def text_input():
    from PySide2.QtWidgets import QDialog, QTextEdit
    
    dialog = QDialog()
    te = QTextEdit(dialog)
    
    dialog.exec()
    return te.toPlainText()


def eval_process_end():
    from PySide2.QtCore import QThread    
    import numpy as np
    
    # prepare data from the operator's thread
    # maybe we have to think about the lifetime of the numpy arrays.
    # They might get destroyed before the plot has been closed.
    a = np.arange(50000000)
    b = np.arange(50000000) * -2
    
    # call the functions in the main thread
    func(a, b)
    print(text_input()) 
