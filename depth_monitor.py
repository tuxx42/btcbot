import threading
import time
import queue
import depth
import logging
import os
from multiprocessing.pool import ThreadPool
log = logging.getLogger(__name__)


def execute_trades(args):
    api, trades, pair = args
    for trade in trades:
        api.execute(trade, pair)


class AsyncResult(threading.Thread):
    def __init__(self, callback):

        super(AsyncResult, self).__init__()

        self.done = threading.Condition()
        self.callback = callback
        self.result = None

    def run(self):
        #log.debug('Async result on %s', self.callback)
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

    def get_depth(self, pair):
        log.debug('Getting depth from %s', self.api)
        self.cmd_q.put([self.api.depth, pair])
        r = AsyncResult(self.res_q.get)
        r.start()
        return r

    def run(self):
        while not self.stop.is_set():
            try:
                cmd = self.cmd_q.get(True, 1.0)
                #log.debug('cmd loop: %s', repr(cmd))
                func = cmd[0]
                cmd = cmd[1:]
                #log.debug('Calling %s', repr(func))
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
                 pair,
                 interval=1,
                 ):

        super(SpreadMonitor, self).__init__()

        log.info('SpreadMonitor init')

        self.total_balance = {}
        self.pair = pair
        self.stop_ev = threading.Event()
        self.interval = float(interval)
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
        balance = self.api1.get_balance()
        self.total_balance['eur'] = balance['eur']
        self.total_balance['btc'] = balance['btc']
        print(api1.name, repr(balance))
        balance = self.api2.get_balance()
        print(api2.name, repr(balance))
        self.total_balance['eur'] += balance['eur']
        self.total_balance['btc'] += balance['btc']
        print('total', repr(self.total_balance))

        #while True:
        #    try:
        #        self.api1.update_balance()
        #        self.api2.update_balance()
        #        return None
        #    except Exception as e:
        #        time.sleep(5)
        #        log.debug(e)
        #        print(e)

    def stop(self):
        self.stop_ev.set()

    def run(self):
        log.info('SpreadMonitor Tread started')
        while not self.stop_ev.is_set():
            try:
                d1 = self.t1.get_depth(self.pair)
                d2 = self.t2.get_depth(self.pair)
                spread = depth.depth.profitable_orders(
                    d1.get(),
                    d2.get(),
                    self.api1.fees,
                    self.api2.fees,
                    #12,
                    #12,
                    #0.02,
                    #0.02
                    self.api1.balance['eur'],
                    self.api2.balance['eur'],
                    self.api1.balance['btc'],
                    self.api2.balance['btc']
                )

                log.debug(spread)
                if 'error' in spread.keys():
                    print(spread['error'])
                    return False

                if spread['profitable']:
                    print(time.strftime("%H:%M:%S"), spread)
                    direction = spread['direction']

                    # alternative 1
                    if direction < 0:
                        api1 = self.api1
                        api2 = self.api2
                    else:
                        api1 = self.api2
                        api2 = self.api1

                    self.order_pool.map(execute_trades,
                                        [[api2,
                                          spread['bids'],
                                          spread['pair']],
                                         [api1,
                                          spread['asks'],
                                          spread['pair']]]
                                        )
                    os.system('beep -f 480 -l 400')
                    balance = self.api1.get_balance()
                    self.total_balance['eur'] -= balance['eur']
                    self.total_balance['btc'] -= balance['btc']
                    print(api1.name, repr(balance))
                    balance = self.api2.get_balance()
                    self.total_balance['eur'] -= balance['eur']
                    self.total_balance['btc'] = round(
                        self.total_balance['btc'] - balance['btc'], 8
                    )
                    print(api2.name, repr(balance))
                    print('total', repr(self.total_balance))
                    break
            except queue.Empty:
                pass
            time.sleep(self.interval)
