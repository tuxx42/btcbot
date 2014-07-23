from datetime import datetime
import logging
import time
from global_vars import gv
log = logging.getLogger(__name__)


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
        r = '[%f, %f]' % (self.value, self.volume)
        return r

#    def __repr__(self):
#        r = self.typ and 'ask' or 'bid'
#        r += ' value(%f)' % self.value
#        r += ' vol(%f)' % self.volume
#        if self.timestamp:
#            r += ', time(%s)' % self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
#        return r

    @staticmethod
    def diff(t1, t2):
        #print(t1)
        #print(t2)
        return t1.value - t2.value


class ask_list(list):
    def __init__(self):
        super().__init__()
        self.total_value = 0
        self.total_volume = 0

    def append(self, ask):
        self.total_value += ask.value * ask.volume
        self.total_volume += ask.volume
        for idx, i in enumerate(self):
            if self[idx].value == ask.value:
                self[idx].volume += ask.volume
                return None
        super().append(ask)


class bid_list(list):
    def __init__(self):
        super().__init__()
        self.total_value = 0
        self.total_volume = 0

    def append(self, bid):
        self.total_value += bid.value * bid.volume
        self.total_volume += bid.volume
        for idx, i in enumerate(self):
            if self[idx].value <= bid.value:
                self[idx].value = bid.value
                self[idx].volume += bid.volume
                return None
            else:
                self[idx].volume += bid.volume
        super().append(bid)


class depth(object):
    def __init__(self, asks=[], bids=[]):
        self.time = time.time()
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
        return list(filter(lambda t: t.value > edge.value,
                           self.bids))

    def get_asks_lower(self, edge):
        return list(filter(lambda t: t.value < edge.value,
                           self.asks))

    def get_weighted_price(self, trades, volume_to_trade):
        weighted_value = 0.0
        vol = volume_to_trade
        for item in trades:
            if item.volume < vol:
                weighted_value += item.value * item.volume
                vol -= item.volume
            else:
                weighted_value += item.value * vol
                break
        weighted_value /= volume_to_trade
        return weighted_value

    @staticmethod
    def profitable_orders(
        depth1,
        depth2,
        cb_fees1,
        cb_fees2,
        ask_limit1,
        ask_limit2,
        bid_limit1,
        bid_limit2
    ):
        # TODO set global threshold value for profitable trades
        #      (currently 0.2)

        res = {'asks': [], 'bids': [], 'profitable': False}

        done = False

        # make sure time of depths are not older than 1 second
        if time.time() - depth1.time > float(gv['depth_timeout']):
            log.error('depth data of api1 too old %f > %f',
                      time.time() - depth1.time, float(gv['depth_timeout']))
            done = True
        elif time.time() - depth2.time > float(gv['depth_timeout']):
            log.error('depth data of api2 too old %f > %f',
                      time.time() - depth2.time, float(gv['depth_timeout']))
            done = True

        if done:
            return res

        mina1 = depth1.get_min_ask()
        maxb1 = depth1.get_max_bid()
        log.debug('min ask 1: %s, max bid 1: %s', mina1, maxb1)

        mina2 = depth2.get_min_ask()
        maxb2 = depth2.get_max_bid()
        log.debug('min ask 2: %s, max bid 2: %s', mina2, maxb2)

        # asks: market sells btc for cur
        # bids: market buys btc for cur
        if mina1 < maxb2:
            ask_depth = depth1.asks
            bid_depth = depth2.bids
            # we need to buy from 1 therefore money needs to be limited
            ask_limit = ask_limit1
            # we need to sell btc on 2 therefore btc needs to be limited
            bid_limit = bid_limit2
            cb_ask_fees = cb_fees1
            cb_bid_fees = cb_fees2
            res['direction'] = 1
        elif mina2 < maxb1:
            ask_depth = depth2.asks
            bid_depth = depth1.bids
            ask_limit = ask_limit2
            bid_limit = bid_limit1
            cb_ask_fees = cb_fees2
            cb_bid_fees = cb_fees1
            res['direction'] = -1
        else:
            return res

        log.debug("ask_depth: %s", ask_depth)
        log.debug("bid_depth: %s", bid_depth)
        log.debug("ask limit: %f", ask_limit)
        log.debug("bid limit: %f", bid_limit)
        # what we want to buy
        our_ask = ask_list()
        # what we want to sell
        our_bid = bid_list()
        bid_depth = list(reversed(bid_depth))
        total_profit = 0

        done = False
        for ask in ask_depth:
            if done:
                break
            for idxb, bid in enumerate(bid_depth):
                log.debug('comparing %s <> %s', ask, bid)
                if ask.value < bid.value:
                    if bid.volume == -1:
                        continue
                    if ask.volume < bid.volume:
                        log.debug('reducing %s by vol %f', bid, ask.volume)
                        bid_depth[idxb].volume -= ask.volume

                        # check if volume exceeds limit
                        if ask.volume > bid_limit:
                            log.warning('BTC limit exceeded %.8f left, need %.8f',
                                        bid_limit, ask.volume)
                            ask.volume = bid_limit
                            log.debug('reducing to vol %f', bid.volume)
                            done = True

                        # how much money we need to spend
                        ask_total = ask.value * ask.volume

                        # check if value exceeds limit
                        if ask_total > ask_limit:
                            log.warning('Money limit exceeded %.8f left, need %.8f',
                                        ask_limit, ask_total)
                            ask.volume = ask_limit / ask.value
                            log.debug('reducing to vol %.8f', ask.volume)
                            done = True

                        profit = bid.value * ask.volume - \
                            ask.value * ask.volume

                        fees_bid = bid.value * ask.volume * cb_bid_fees()
                        fees_ask = ask.value * ask.volume * cb_ask_fees()
                        fees = fees_bid + fees_ask

                        log.debug('profit: %f, fees: %f, diff: %f',
                                  profit, fees, profit - fees)

                        # TODO sum volumes for same prices
                        if profit - fees > 0:
                            # we buy btc -> we need money
                            # reduce remaining money
                            ask_limit -= ask.value * ask.volume
                            log.info('Money Left %.8f', ask_limit)
                            our_bid.append(trade(ask.value,
                                                 ask.volume, typ=trade.BID))
                            log.debug('appending to our_bid %s', our_bid[-1])
                            # we sell btc -> we need btc
                            # reduce remaining btc
                            bid_limit -= ask.volume
                            log.info('btc Left %.8f', bid_limit)
                            our_ask.append(trade(bid.value,
                                                 ask.volume, typ=trade.ASK))
                            log.debug('appending to our_ask %s', our_ask[-1])
                            res['profitable'] = True
                            total_profit += profit - fees
                        else:
                            done = True
                        # goto next ask
                        break
                    elif ask.volume >= bid.volume:
                        log.debug('reducing %s by vol %f', ask, bid.volume)
                        ask.volume -= bid.volume

                        # check if volume exceeds limit
                        if bid.volume > bid_limit:
                            log.warning('BTC limit exceeded %.8f left, need %.8f',
                                        bid_limit, bid.volume)
                            bid.volume = bid_limit
                            log.debug('reducing to vol %f', bid.volume)
                            done = True

                        # how much money we need to spend
                        ask_total = ask.value * bid.volume

                        # check if value exceeds limit
                        if ask_total > ask_limit:
                            log.warning('Money limit exceeded %.8f left, need %.8f',
                                        ask_limit, ask_total)
                            bid.volume = ask_limit / ask.value
                            log.debug('reducing to vol %.8f', bid.volume)
                            done = True

                        profit = bid.value * bid.volume - \
                            ask.value * bid.volume

                        fees_bid = bid.value * bid.volume * cb_bid_fees()
                        fees_ask = ask.value * bid.volume * cb_ask_fees()
                        fees = fees_bid + fees_ask

                        log.debug('profit: %f, fees: %f, diff: %f',
                                  profit, fees, profit - fees)
                        # TODO sum volumes or same prices
                        if profit - fees > 0:

                            # Need to spend money
                            ask_limit -= ask.value * bid.volume
                            log.info('Money Left %.8f', ask_limit)
                            our_bid.append(trade(ask.value,
                                                 bid.volume, typ=trade.BID))
                            log.debug('appending to our_bid %s', our_bid[-1])
                            # Need to spend btc
                            bid_limit -= bid.volume
                            log.info('btc Left %.8f', bid_limit)
                            our_ask.append(trade(bid.value,
                                                 bid.volume, typ=trade.ASK))
                            log.debug('appending to our_ask %s', our_ask[-1])
                            log.debug('removing %s', bid)
                            bid_depth[idxb].volume = -1
                            #bid_depth.remove(bid)
                            res['profitable'] = True
                            total_profit += profit - fees
                        else:
                            done = True
                        # continue checking next bid
                else:
                    # remove consumed bids
                    bids = [bid for bid in bid_depth if bid.volume == -1]
                    for bid in bids:
                        bid_depth.remove(bid)
                    break

        # sanity check
        if res['profitable']:
            res['asks'] = our_ask
            res['bids'] = our_bid
            res['total_profit'] = round(total_profit, 3)
            #assert(len(our_ask) > 0 and len(our_bid) > 0)

            ask_price_avg = round(our_ask.total_value, 8)
            bid_price_avg = round(our_bid.total_value, 8)
            ask_volume = round(our_bid.total_volume, 8)
            bid_volume = round(our_ask.total_volume, 8)

            if ask_price_avg < bid_price_avg:
                log.error("DEPTH ERROR: our_ask_price: %f, our_bid_price: %f",
                          ask_price_avg, bid_price_avg)
                res['error'] = "average ask price is not larger than bid price"

            if ask_volume <= 0:
                log.error("DEPTH ERROR: ask_volume is negative", ask_volume)
                res['error'] = "ask_volume is negative"

            if bid_volume <= 0:
                log.error("DEPTH ERROR: bid_volume is negative", bid_volume)
                res['error'] = "bid_volume is negative"

            if abs(ask_volume - bid_volume) >= 0.001:
                log.error("DEPTH ERROR: ask_volume: %f, bid_volume: %f",
                          ask_volume, bid_volume)
                res['error'] = "ask and bid volume not equivalent"

            if total_profit <= 0:
                log.error("DEPTH ERROR: total_profit is negative %f",
                          total_profit)
                res['error'] = "total profit is negative"

            if our_ask.total_volume <= 0:
                log.error("DEPTH ERROR: trade_vol is negative %f",
                          our_ask.total_volume)
                res['error'] = "trade_vol is negative"

            if our_bid.total_value <= 0:
                log.error("DEPTH ERROR: bid_value is negative %f",
                          our_bid.total_value)
                res['error'] = "bid_value is negative"

            # res['vol_ask'] is btc vol
            res['trade_vol'] = round(our_ask.total_volume, 8)
            # res['vol_bid'] is eur vol
            res['pair'] = gv['pair']
            res['ask_total_value'] = our_ask.total_value
            res['bid_total_value'] = our_bid.total_value
            res['profitability_ratio'] = round(total_profit / our_ask.total_value * 100.0, 4)

        return res

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
