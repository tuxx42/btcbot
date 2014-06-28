import time


class trade(object):

    BID = 0
    ASK = 1

    def __init__(self, value=0.0, amount=0.0, timestamp=0, typ=BID):
        self.value = float(value)
        self.amount = float(amount)
        #self.timestamp = time.mktime(timestamp)
        self.typ = typ

    def __repr__(self):
        r = self.typ and 'ASK: ' or 'BID: '
        r += 'value : %f, ' % self.value
        r += 'amount: %f' % self.amount
        #r += '\tTIME  : %f\n' % self.time
        return r


class depth(object):
    def __init__(self, asks=[], bids=[]):
        self.asks = map(lambda t: trade(*t, typ=trade.ASK), asks)
        self.bids = map(lambda t: trade(*t, typ=trade.BID), bids)
        self.timestamp = time.time()

    def diff(self, other):
        pass

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
