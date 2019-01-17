import time

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ProcessDialog(QDialog):
    success_slot = QtCore.pyqtSignal(object)
    fail_slot = QtCore.pyqtSignal(object)
    ignore_slot = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent, flags=Qt.Window | Qt.WindowTitleHint)

        self.__can_close = False
        self.__total = 0
        self.__current = 0
        self.__success_text = []
        self.__fail_text = []
        self.__ignore_text = []
        self.__ignore = 0
        self.__success = 0
        self.__fail = 0
        self.__finish = False

        self.__ui()

        self.success_slot.connect(self.__addSuccessText)
        self.fail_slot.connect(self.__addFailText)
        self.ignore_slot.connect(self.__addIgnoreText)

        self.__initCloseDialogTimer()

        timer = self.timer = QTimer()
        timer.setSingleShot(False)
        timer.setInterval(500)
        timer.timeout.connect(self.__update_ui)
        timer.start()

    def __ui(self):
        self.setWindowTitle('请稍候')
        self.setMinimumSize(600, 400)
        hbox = QVBoxLayout()
        self.setLayout(hbox)

        self.bar = QProgressBar()
        hbox.addWidget(self.bar)
        self.bar.setTextVisible(True)
        self.bar.setAlignment(Qt.AlignCenter)

        hbox.addWidget(QLabel('结果'))
        stop_btn = QPushButton('停止')

        def stop():
            self.__current = 100
            self.__finish = True
            self.done(QDialog.Rejected)

        stop_btn.clicked.connect(stop)
        hbox.addWidget(stop_btn)
        self.__text_view = QTextBrowser()
        self.__text_view.setLineWrapMode(QTextEdit.NoWrap)
        hbox.addWidget(self.__text_view)

        self.__text_v_scrollbar: QScrollBar = self.__text_view.verticalScrollBar()
        self.__text_h_scrollbar: QScrollBar = self.__text_view.horizontalScrollBar()

    def setTotal(self, total: int):
        self.__total = total
        self.__calc_current()

    def current(self):
        return self.__current

    def __calc_current(self):
        value = 1 if self.__ignore > 0 else 0
        current = self.__success + self.__fail
        if self.__total > 0 and current > 0:
            value = current / self.__total

        self.__current = int(value * 100)
        if self.__current > 100:
            self.__current = 100

        self.__finish = self.__current >= 100
        return self.__current

    def __update_ui(self):

        if self.__finish:
            self.timer.stop()
            return
        print('更新ui')

        self.bar.setValue(self.__current)
        self.bar.setFormat('进度：{}%'.format(self.__current))
        self.setWindowTitle(str(self.__current) + '%')

        v_value = self.__text_v_scrollbar.value()
        h_value = self.__text_h_scrollbar.value()

        text = '====失败 {}====\n  '.format(self.__fail)
        text += '\n  '.join(self.__fail_text)

        text += '\n\n====跳过上传 {}====\n  '.format(self.__ignore)
        text += '\n  '.join(self.__ignore_text)

        text += '\n\n====成功 {}====\n  '.format(self.__success)
        text += '\n  '.join(self.__success_text)
        self.__text_view.setPlainText(text)

        self.__text_v_scrollbar.setValue(v_value)
        self.__text_h_scrollbar.setValue(h_value)

    def setTimeoutClose(self, millisecond: int):
        self.__timeout_close = millisecond

    def __initCloseDialogTimer(self):
        self.__timeout_close = 0

        timer = self.close_timer = QTimer()
        timer.setSingleShot(False)
        timer.setInterval(1000)
        self.__last_check_close_time = 0

        def worker():
            if not self.__finish or self.__timeout_close == 0:
                return
            last = time.time() - self.__last_check_close_time
            if last >= self.__timeout_close:
                self.close()

        timer.timeout.connect(worker)
        timer.start()

    def addSuccessText(self, msg: str):
        self.success_slot.emit(msg)

    def addFailText(self, msg: str):
        self.fail_slot.emit(msg)

    def addIgnoreText(self, msg: str):
        self.ignore_slot.emit(msg)

    def __addSuccessText(self, msg: str):
        self.__success_text.append(msg)
        self.__success += 1
        self.__calc_current()

    def __addFailText(self, msg: str):
        self.__fail_text.append(msg)
        self.__fail += 1
        self.__calc_current()

    def __addIgnoreText(self, msg: str):
        self.__ignore_text.append(msg)
        self.__ignore += 1

    def done(self, p_int):
        print('done', self.__current, self.__current < 100)
        if self.__current < 100:
            return
        QDialog.done(self, p_int)

    def closeEvent(self, eve: QCloseEvent):
        print('closeEvent', self.__current, self.__current < 100)
        if self.__current < 100:
            eve.ignore()
            return
        QDialog.closeEvent(self, eve)
