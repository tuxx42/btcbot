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

    @staticmethod
    def diff(t1, t2):
        print(t1)
        print(t2)
        return t1.value - t2.value


class depth(object):
    def __init__(self, asks=[], bids=[]):
        self.asks = sorted(map(lambda t: trade(*t, typ=trade.ASK), asks))
        self.bids = sorted(map(lambda t: trade(*t, typ=trade.BID), bids))

    def diff(self, other):
        pass

    def total_volume(self, n=-1):
        return {'ask': sum([a.volume for a in self.asks[0:n]]),
                'bid': sum([a.volume for a in self.asks[0:n]])}

    def get_min_ask(self):
        return self.asks[0]

    def get_max_bid(self):
        return self.bids[-1]

    def get_bids_bigger(self, edge):
        return filter(lambda t: t.value > edge, self.bids)

    def get_asks_lower(self, edge):
        return filter(lambda t: t.value < edge, self.asks)

    @staticmethod
    def spread(d1, d2):
        minb1 = d1.get_min_ask()
        minb2 = d2.get_min_ask()
        maxa1 = d1.get_max_bid()
        maxa2 = d2.get_max_bid()
        r = {}
        r['12'] = trade.diff(maxa1, minb2)
        r['21'] = trade.diff(maxa2, minb1)
        if r['12'] > 0:
            r['12_open'] = d1.get_bids_bigger(minb2)
        if r['21'] > 0:
            r['21_open'] = d2.get_bids_bigger(minb1)
        return r
        #n = min(len(d1.asks), len(d2.asks))
        #a1 = sum(a.value * a.volume for a in d1.asks[0:n])
        #a2 = sum(a.value * a.volume for a in d2.asks[0:n])
        #ask_spread = a1 / d1.total_volume(n)['ask'] - \
        #    a2 / d2.total_volume(n)['ask']
        #return ask_spread

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
