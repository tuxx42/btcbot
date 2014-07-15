import threading
import time
import queue
import depth
import logging
from multiprocessing.pool import ThreadPool
from global_vars import gv
log = logging.getLogger(__name__)


def execute_trades(api, trades):
    for trade in trades:
        api.execute(trade)


class AsyncResult(threading.Thread):
    def __init__(self, callback):

        super(AsyncResult, self).__init__()

        self.done = threading.Condition()
        self.callback = callback
        self.result = None

    def run(self):
        log.debug('Async result on %s', self.callback)
        self.result = self.callback()
#        log.debug('Async result %s retrieved', self.result)
        self.done.acquire()
        self.done.notify()
        self.done.release()

    def get(self):
        self.done.acquire()
        while not self.result:
            self.done.wait()
        self.done.release()
        return self.result


class Monitor(threading.Thread):
    def __init__(self, api, cmd_q, res_q):

        super(Monitor, self).__init__()

        self.api = api
        self.cmd_q = cmd_q
        self.res_q = res_q
        self.stop = threading.Event()

    def stop(self):
        self.stop.set()

    def get_depth(self):
        log.debug('Getting depth from %s', self.api)
        self.cmd_q.put([self.api.depth, ])
        r = AsyncResult(self.res_q.get)
        r.start()
        return r

    def run(self):
        while not self.stop.is_set():
            try:
                cmd = self.cmd_q.get(True, 1.0)
                log.debug('cmd loop: %s', repr(cmd))
                func = cmd.pop()
                log.debug('Calling %s', repr(func))
                res = func(*cmd)
                #log.debug('GOT RESULT: %s', res)
                self.res_q.put(res)
                self.cmd_q.task_done()
            except queue.Empty:
                pass


class SpreadMonitor(threading.Thread):

    def __init__(self,
                 api1,
                 api2,
                 interval=1,
                 ):

        super(SpreadMonitor, self).__init__()

        log.info('SpreadMonitor init')

        self.stop_ev = threading.Event()
        self.interval = interval
        self.api1 = api1
        self.cmd_q1 = queue.Queue()
        self.res_q1 = queue.Queue()
        self.t1 = Monitor(api1, self.cmd_q1, self.res_q1)
        self.t1.setDaemon(True)
        self.t1.start()

        self.api2 = api2
        self.cmd_q2 = queue.Queue()
        self.res_q2 = queue.Queue()
        self.t2 = Monitor(api2, self.cmd_q2, self.res_q2)
        self.t2.setDaemon(True)
        self.t2.start()

        self.order_pool = ThreadPool(2)
        self.api1.update_balance()
        self.api2.update_balance()

    def stop(self):
        self.stop_ev.set()

    def run(self):
        log.info('SpreadMonitor Tread started')
        while not self.stop_ev.is_set():
            try:
                d1 = self.t1.get_depth()
                d2 = self.t2.get_depth()
                spread = depth.depth.profitable_orders(d1.get(),
                                                       d2.get(),
                                                       self.api1.fees,
                                                       self.api2.fees)
                log.debug(spread)
                if 'error' in spread.keys():
                    print(spread['error'])
                    return False

                if spread['profitable']:
                    print(time.strftime("%H:%M:%S"), spread)
                    direction = spread['direction']
                    vol_ask = spread['vol_ask']
                    vol_bid = spread['vol_bid']

                    # alternative 1
                    if direction < 0:
                        api1 = self.api1
                        api2 = self.api2
                    else:
                        api1 = self.api2
                        api2 = self.api1

                    if api1.balance_bid > vol_ask and \
                            api2.balance_ask > vol_bid:
                        self.order_pool.map(execute_trades,
                                            [[api2, spread['bids']],
                                             [api1, spread['asks']]]
                                            )

                    # alternative 2
#                    if direction < 0:
#                        if self.api1.balance_bid > vol_ask and \
#                                self.api2.balance_ask > vol_bid:
#                            self.order_pool.map(execute_trades,
#                                                [[self.api2, spread['bids']],
#                                                 [self.api1, spread['asks']]]
#                                                )
#                    else:
#                        if self.api2.balance_bid > vol_ask and \
#                                self.api1.balance_ask > vol_bid:
#                            self.order_pool.map(execute_trades,
#                                                [[self.api1, spread['bids']],
#                                                 [self.api2, spread['asks']]]
#                                                )
                    self.api1.update_balance()
                    self.api2.update_balance()
            except queue.Empty:
                pass
            time.sleep(float(gv['depth_interval']))
