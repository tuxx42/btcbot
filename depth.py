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

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        r = self.typ and 'ASK: ' or 'BID: '
        r += 'price(%f)' % self.value
        r += ', vol(%f)' % self.volume
#        if self.timestamp:
#            r += ', time(%s)' % self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return r

    @staticmethod
    def diff(t1, t2):
        #print(t1)
        #print(t2)
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
        print (edge)
        return list(filter(lambda t: t.value > edge.value, self.bids))

    def get_asks_lower(self, edge):
        return list(filter(lambda t: t.value > edge.value, self.bids))

    @staticmethod
#    def spread(**kwargs):
#        kwargs['api1'].get_depth()
#        kwargs['api2'].get_depth()
#
#        r = {}
#        depth1 = kwargs['api1'].curdepth[kwargs['pair']][0]
#        depth2 = kwargs['api2'].curdepth[kwargs['pair']][0]
#
#        if depth2.get_min_ask() < depth1.get_max_bid():
#            print('buy from api2 sell api1')
#            depth = {'buy': depth2, 'sell': depth1}
#            r['profitable'] = True
#        elif depth1.get_min_ask() < depth2.get_max_bid():
#            print('buy from api1 sell api2')
#            depth = {'buy': depth1, 'sell': depth2}
#            r['profitable'] = True
#        else:
#            r['profitable'] = False
#            return r
#
#        for ask in depth['buy'].asks:
#            print (ask)

#        for i in range(len(depth['buy'].asks)):
#            if depth['buy'].asks[i] > depth['sell'].bids[-(i+1)]:
#                print(depth['buy'].asks[i], depth['sell'].bids[-(i+1)])
#
#        return (r)
#
#    def spread(**kwargs):
#        depth = {}
#        vals = {}
#        depth['api1'] = kwargs['api1'].curdepth[kwargs['pair']][0]
#        depth['api2'] = kwargs['api2'].curdepth[kwargs['pair']][0]
#
#        vals['api1'] = {'min_ask': depth['api1'].get_min_ask(),
#                        'max_bid': depth['api1'].get_max_bid()}
#        vals['api2'] = {'min_ask': depth['api2'].get_min_ask(),
#                        'max_bid': depth['api2'].get_max_bid()}
#
#        r = {}
#        diff = trade.diff(vals['api1']['max_bid'], vals['api2']['min_ask'])
#        if diff > 0:
#            r['buy'] = kwargs['api1']
#            r['sell'] = kwargs['api2']
#            buys = depth['api1'].get_bids_bigger(vals['api2']['min_ask'])
#            sells = depth['api2'].get_asks_lower(vals['api1']['max_bid'])
#            print(buys)
#            print(sells)
#
#        diff = trade.diff(vals['api2']['max_bid'], vals['api1']['min_ask'])
#        if diff > 0:
#            r['buy'] = kwargs['api2']
#            r['sell'] = kwargs['api1']
#            buys = depth['api2'].get_bids_bigger(vals['api1']['min_ask'])
#            sells = depth['api1'].get_bids_bigger(vals['api2']['max_bid'])
#            print(buys)
#            print(sells)
#
#        return (r)
    def spread(**kwargs):
        try:
            kwargs['api1'].get_depth()
            d1 = kwargs['api1'].curdepth[kwargs['pair']][0]
        except:
            raise Exception('no depth for \'%s(%s)\'' %
                            (kwargs['api1'].name, kwargs['pair']))
        try:
            kwargs['api2'].get_depth()
            d2 = kwargs['api2'].curdepth[kwargs['pair']][0]
        except:
            raise Exception('no depth for \'%s(%s)\'' %
                            (kwargs['api2'].name, kwargs['pair']))

        minb1 = d1.get_min_ask()
        minb2 = d2.get_min_ask()
        maxa1 = d1.get_max_bid()
        maxa2 = d2.get_max_bid()

        r = {}
        if trade.diff(maxa1, minb2) > 0:
            r['buy'] = kwargs['api1']
            r['sell'] = kwargs['api2']
            r['profit'] = trade.diff(maxa1, minb2)
            r['open'] = d1.get_bids_bigger(minb2)
            r['profitable'] = True
        elif trade.diff(maxa2, minb1) > 0:
            r['buy'] = kwargs['api2']
            r['sell'] = kwargs['api1']
            r['profit'] = trade.diff(maxa2, minb1)
            r['open'] = d2.get_bids_bigger(minb1)
            r['profitable'] = True
        else:
            r['profitable'] = False

        if 'open' in r.keys():
            r['volume'] = sum(map(lambda t: t.volume, r['open']))

        return r

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
