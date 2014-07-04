import threading
import queue
import depth
import logging
log = logging.getLogger(__name__)


class AsyncResult(threading.Thread):
    def __init__(self, callback):
        self.done = threading.Condition()
        self.callback = callback

    def run(self):
        self.result = self.callback()
        self.done.notify()

    def get(self):
        self.done.wait()
        return self.result


class Monitor(threading.Thread):
    def __init__(self, api, cmd_q, res_q):
        self.api = api
        self.cmd_q = cmd_q
        self.res_q = res_q
        self.stop = threading.Event()

    def stop(self):
        self.stop.set()

    def get_depth(self):
        self.cmd_q.put([self.api.get_depth, ])
        r = AsyncResult(self.res_q.get)
        r.start()
        return r

    def run(self):
        while not self.stop.is_set():
            try:
                cmd = self.cmd_q.get(True, 1.0)
                func = cmd.pop()
                res = func(*cmd)
                self.res_q.put(res)
                self.cmd_q.task_done()
            except queue.timeout:
                pass


class SpreadMonitor(threading.Thread):

    def __init__(self,
                 api1,
                 api2,
                 ):

        log.info('SpreadMonitor init')
        self.api1 = api1
        self.cmd_q1 = queue.Queue()
        self.res_q1 = queue.Queue()
        self.t1 = Monitor(api1, self.cmd_q1, self.res_q1)
        self.t1.start()

        self.api2 = api2
        self.cmd_q2 = queue.Queue()
        self.res_q2 = queue.Queue()
        self.t2 = Monitor(api2, self.cmd_q2, self.res_q2)
        self.t2.start()

    def run(self):
        log.info('SpreadMonitor Tread started')
        while True:
            d1 = self.t1.get_depth()
            d2 = self.t2.get_depth()
            spread = depth.spread(d1.get(), d2.get())
            if spread['profitable']:
                print(spread)
