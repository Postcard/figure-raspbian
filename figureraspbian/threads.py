from threading import Thread, Event, RLock


_THREADS = set()

rlock = RLock()


def threads_shutdown():
    while _THREADS:
        for t in _THREADS.copy():
            t.stop()


class StoppableThread(Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.stopping = Event()
        super(StoppableThread, self).__init__(group, target, name, args, kwargs)

    def start(self):
        self.stopping.clear()
        _THREADS.add(self)
        super(StoppableThread, self).start()

    def stop(self):
        self.stopping.set()
        self.join()

    def join(self):
        super(StoppableThread, self).join()
        _THREADS.discard(self)


class Interval(StoppableThread):

    def __init__(self, sec, func):
        super(Interval, self).__init__(target=self.set_interval, args=(func, sec))
        self.daemon = True

    def set_interval(self, sec, func):
        while not self.stopping.wait(sec):
            try:
                func()
            except:
                pass
