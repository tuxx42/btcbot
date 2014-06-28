from datetime import datetime


class trade(object):

    BID = 0
    ASK = 1

    def __init__(self, value=0.0, volume=0.0, timestamp=0, typ=BID):
        self.value = float(value)
        self.volume = float(volume)
        if timestamp:
            self.timestamp = datetime.fromtimestamp(float(timestamp))
        else:
            self.timestamp = None
        self.typ = typ

    def __eq__(self, other):
        # TODO
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        r = self.typ and 'ASK: ' or 'BID: '
        r += 'value %f' % self.value
        r += ', volume: %f' % self.volume
        if self.timestamp:
            r += ', time: %s' % self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return r


class depth(object):
    def __init__(self, asks=[], bids=[]):
        self.asks = sorted(map(lambda t: trade(*t, typ=trade.ASK), asks))
        self.bids = sorted(map(lambda t: trade(*t, typ=trade.BID), bids))

    def diff(self, other):
        pass

    def total_volume(self, n=-1):
        return {'ask': sum([a.volume for a in self.asks[0:n]]),
                'bid': sum([a.volume for a in self.asks[0:n]])}

    @staticmethod
    def spread(d1, d2):
        n = min(len(d1.asks), len(d2.asks))
        a1 = sum(a.value * a.volume for a in d1.asks[0:n])
        a2 = sum(a.value * a.volume for a in d2.asks[0:n])
        ask_spread = a1 / d1.total_volume(n)['ask'] - \
            a2 / d2.total_volume(n)['ask']
        return ask_spread

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
