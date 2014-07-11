import threading
import queue


class TradeExecutor(object):
    def __init__(self,
                 api,
                 trades):
        super().__init__()
        self.api = api
        self.trades = trades

    def run(self):
        while True:
            try:
                self.in_q.get(True, 0.01)

            except queue.TimeoutError:
                pass
