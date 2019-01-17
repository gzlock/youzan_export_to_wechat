import threading
import time
import types

from PyQt5.QtCore import *

Types = [types.MethodType, types.FunctionType, types.BuiltinFunctionType]


class Pool:
    pool_change_slot = pyqtSignal(object)

    def __init__(self, number, check_time: float = 0.1, start: bool = False, callback=None):
        self.number = number
        self.__tasks = []
        self.__threads = []
        self.__wait = False
        self.__is_started = start
        if check_time <= 0:
            check_time = 0.1
        self.__check_time = check_time
        self.__callback = callback

        self.__daemon_thread = threading.Thread(target=self.__daemon)
        self.__daemon_thread.start()

    def addTask(self, func, callback=None, *args, **kwargs):
        # print('add task', args, kwargs)
        self.__tasks.append((func, args, kwargs, callback))
        if self.__is_started:
            self.__next_task__()

    def setCallBack(self, callback):
        self.__callback = callback

    def start(self):
        self.__is_started = True
        self.__next_task__()

    def pause(self):
        self.__is_started = False

    def clear(self):
        self.__tasks.clear()

    def wait(self):
        while 1:
            time.sleep(self.__check_time)
            if not self.__is_started or (len(self.__tasks) == 0 and len(self.__threads) == 0):
                break

    def __daemon(self):
        self.wait()
        if callable(self.__callback):
            self.__callback()

    def wait_number(self):
        return len(self.__tasks)

    def __wrapper__(self):
        task_len = len(self.__tasks)
        if task_len > 0:
            task = self.__tasks.pop(0)
            args = task[1]
            kargs = task[2]
            callback = task[3]
            task = task[0]
            res = task(*args, **kargs)
            if callback and callable(callback):
                callback(res)

        thread = threading.current_thread()
        self.__threads.remove(thread)
        self.__next_task__()

    def __next_task__(self):
        if not self.__is_started:
            return
        task_len = len(self.__tasks)
        thread_len = len(self.__threads)
        # print('__next_task__', {'task': task_len, 'thread': thread_len})
        if thread_len < self.number and task_len > 0:
            total = self.number - thread_len
            for i in range(total):
                thread = threading.Thread(target=self.__wrapper__)
                self.__threads.append(thread)
                thread.start()


class Queue(Pool):
    def __init__(self):
        super(Queue, self).__init__(number=1)
