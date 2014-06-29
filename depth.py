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

    def get_bids_higher(self, edge):
        print (edge)
        return list(filter(lambda t: t.value > edge.value,
                           self.bids))

    def get_asks_lower(self, edge):
        return list(filter(lambda t: t.value < edge.value,
                           self.asks))

#    @staticmethod
#    def spread(api1=None, api2=None):
#        depth1 = api1.get_depth()
#        depth2 = api2.get_depth()

    @staticmethod
    def spread(**kwargs):
        kwargs['api1'].get_depth()
        kwargs['api2'].get_depth()

        fee1 = kwargs['api1'].get_fees()
        fee2 = kwargs['api2'].get_fees()

        r = {}
        depth1 = kwargs['api1'].curdepth[kwargs['pair']][0]
        depth2 = kwargs['api2'].curdepth[kwargs['pair']][0]

        mina1 = depth1.get_min_ask()
        maxb1 = depth1.get_max_bid()
        #print('Min Ask 1: %s' % mina1)
        #print('Max Bid 1: %s' % maxb1)

        mina2 = depth2.get_min_ask()
        maxb2 = depth2.get_max_bid()
        #print('Min Ask 2: %s' % mina2)
        #print('Max Bid 2: %s' % maxb2)

        # mininum sell price (ask) on api1 is lower than maximum buy price
        # (bid) on api2
        # => buy from 1 all lower priced asks than maximum bid on 2
        # => sell on 2 all higher priced bids than minimum ask on 1
        if mina1 < maxb2:
            #print('buy from api1 sell api2')
            trades = {
                'buy_api': kwargs['api1'],
                'sel_api': kwargs['api2'],
                'we_buy': depth1.get_asks_lower(maxb2),
                'we_sell': depth2.get_bids_higher(mina1),
                'max_bid': maxb2,
                'min_ask': mina1,
            }
            r['profitable'] = True
        elif mina2 < maxb1:
            #print('buy from api2 sell api1')
            trades = {
                'buy_api': kwargs['api2'],
                'sel_api': kwargs['api1'],
                'we_buy': depth2.get_asks_lower(maxb1),
                'we_sell': depth1.get_bids_higher(mina2),
                'max_bid': maxb1,
                'min_ask': mina2,
            }
            r['profitable'] = True
        else:
            r['profitable'] = False
            return r

        #print('BUY')
        #print('\n'.join(map(repr, trades['we_buy'])))
        #print('SELL')
        #print('\n'.join(map(repr, trades['we_sell'])))

        volume_to_sell = sum(
            map(lambda t: t.volume, trades['we_sell']))
        volume_to_buy = sum(
            map(lambda t: t.volume, trades['we_buy']))
        volume_to_trade = min(volume_to_sell, volume_to_buy)

        weighted_value_sell = 0.0
        vol = 0.0
        for ask in trades['we_ask']:
            if vol < volume_to_trade:
                break

        #sum(map(lambda t: t.volume * t.value, trades['we_sell'])) / \
        #    volume_to_sell
        #weighted_value_buy = sum(map(lambda t: t.volume * t.value, trades['we_buy'])) / \
        #    volume_to_buy

        print('wv sell: %f', weighted_value_sell)
        print('wv buy: %f', weighted_value_buy)
        print('Volume to sell: %f' % volume_to_sell)
        print('Volume to buy: %f' % volume_to_buy)
        print('Volume to trade: %f' % volume_to_trade)

        order_buy = trade(
            value=trades['max_bid'].value,
            volume=volume_to_trade,
            typ=trade.BID
        )
        print('BUY ORDER (%s)' % trades['buy_api'])
        print(order_buy)

        orders_sell = []
        for bid in reversed(trades['we_sell']):
            if volume_to_trade < bid.volume:
                bid.volume = volume_to_trade
            order_sell = trade(
                value=bid.value,
                volume=bid.volume,
                typ=trade.ASK
            )
            orders_sell.append(order_sell)
            volume_to_trade -= bid.volume
            #print('SEL ORDER (%s)' % trades['sel_api'])
            #print(order_sell)
            if volume_to_trade <= 0.0:
                break

        profit = {}
        profit['gross'] = weighted_value_sell - weighted_value_buy
        profit['net'] = weighted_value_sell * volume_to_sell * (1.0 - trades['sel_api'].get_fees()) + \
            weighted_value_buy * volume_to_buy * (1.0 - trades['buy_api'].get_fees())
        print(profit)


        #print('Profit:')
        #for ask in trades['buy']:
        #    print (ask)

        r['order_buy'] = order_buy
        r['api_buy'] = trades['buy_api']
        r['orders_sell'] = orders_sell
        r['api_sell'] = trades['sel_api']
        print(r)
        return (r)
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
    def spread2(**kwargs):
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
