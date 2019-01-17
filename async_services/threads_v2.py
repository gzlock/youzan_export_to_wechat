import threading
import time
import types

from PyQt5 import QtCore
from PyQt5.QtCore import *

Types = [types.MethodType, types.FunctionType, types.BuiltinFunctionType]


class Signals(QObject):
    finished = pyqtSignal(object, object, object)


class WorkThread(threading.Thread):
    def __init__(self):
        super(WorkThread, self).__init__()
        self.signals = Signals()

    def setTask(self, task):
        self.task = task

    def run(self):
        res = None
        err = None
        if self.task:
            task = self.task[0]
            args = self.task[1]
            kargs = self.task[2]
            try:
                res = task(*args, **kargs)
            except Exception as e:
                err = e

        self.signals.finished.emit(self, res, err)
        print('thread res', res)


class Pool(QObject):

    def __init__(self, number, start: bool = False, callback=None):
        super(Pool, self).__init__()
        self.number = number
        self.__tasks = []
        self.__threads = []
        self.__wait = False
        self.__finish = False
        self.__is_started = start
        self.__callback = callback

    def addTask(self, func, callback=None, *args, **kwargs):
        # print('add task', args, kwargs)
        self.__tasks.append((func, args, kwargs, callback))
        if self.__is_started and len(self.__threads) == 0:
            self.__start()

    def setCallBack(self, callback):
        self.__callback = callback

    def start(self):
        self.__is_started = True
        self.__finish = False
        self.__start()

    def __start(self):
        if not self.__is_started:
            return
        task_len = len(self.__tasks)
        thread_len = len(self.__threads)
        # print('__next_task__', {'task': task_len, 'thread': thread_len})
        if thread_len < self.number and task_len > 0:
            total = self.number - thread_len
            print('total', total)
            for i in range(total):
                if len(self.__tasks) == 0:
                    break
                thread = WorkThread()
                thread.signals.finished.connect(self.__thread_finish)
                self.__threads.append(thread)
                self.__next_task__(thread)

    def pause(self):
        self.__is_started = False

    def clear(self):
        self.__tasks.clear()

    def wait_number(self):
        return len(self.__tasks)

    def working_number(self):
        return len(self.__threads)

    def __next_task__(self, thread):
        if not self.__is_started or len(self.__tasks) == 0:
            return
        thread.setTask(self.__tasks.pop(0))
        thread.start()

    def __thread_finish(self, *args):
        thread = args[0]
        err = args[1]
        res = args[2]
        print('__thread_finish', res)
        if not self.__is_started:
            return
        if len(self.__tasks) == 0:
            self.__threads.remove(thread)
            if len(self.__threads) == 0:
                self.__finish = True
                if callable(self.__callback):
                    self.__callback()
            return

        self.__next_task__(thread)


class Queue(Pool):
    def __init__(self):
        super(Queue, self).__init__(number=1)
