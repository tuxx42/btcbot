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
    def prof_orders(depth1, depth2, cb_fees1, cb_fees2):
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

        if mina1 < maxb2:
            ask_depth = depth1.asks
            bid_depth = depth2.bids
            cb_ask_fees = cb_fees1
            cb_bid_fees = cb_fees2
        elif mina2 < maxb1:
            ask_depth = depth2.asks
            bid_depth = depth1.bids
            cb_ask_fees = cb_fees2
            cb_bid_fees = cb_fees1
        else:
            return res

        log.debug("ask_depth: %s", ask_depth)
        log.debug("bid_depth: %s", bid_depth)
        # what we want to buy
        our_ask = []
        # what we want to sell
        our_bid = []
        bid_depth = list(reversed(bid_depth))
        total_profit = 0

        done = False
        for ask in ask_depth:
            if done:
                break
            for idxb, bid in enumerate(bid_depth):
                log.debug('comparing %s <> %s', ask, bid)
                if ask.value < bid.value:
                    if ask.volume < bid.volume:
                        log.debug('reducing %s by vol %f', bid, ask.volume)
                        bid_depth[idxb].volume -= ask.volume
                        profit = bid.value * ask.volume - \
                            ask.value * ask.volume
                        fees_bid = bid.value * ask.volume * cb_bid_fees()
                        fees_ask = ask.value * ask.volume * cb_ask_fees()
                        fees = fees_bid + fees_ask
                        log.debug('profit: %f, fees: %f, diff: %f',
                                  profit, fees, profit - fees)
                        total_profit += profit - fees
                        # TODO sum volumes for same prices
                        if profit - fees > 0:
                            our_bid.append(trade(ask.value,
                                                 ask.volume, typ=trade.ASK))
                            log.debug('appending to our_bid %s', our_bid[-1])
                            our_ask.append(trade(bid.value,
                                                 ask.volume, typ=trade.BID))
                            log.debug('appending to our_ask %s', our_ask[-1])
                            res['profitable'] = True
                        else:
                            done = True
                        # goto next ask
                        break
                    elif ask.volume >= bid.volume:
                        log.debug('reducing %s by vol %f', ask, bid.volume)
                        ask.volume -= bid.volume
                        profit = bid.value * bid.volume - \
                            ask.value * bid.volume
                        fees_bid = bid.value * bid.volume * cb_bid_fees()
                        fees_ask = ask.value * bid.volume * cb_ask_fees()
                        fees = fees_bid + fees_ask
                        log.debug('profit: %f, fees: %f, diff: %f',
                                  profit, fees, profit - fees)
                        total_profit += profit - fees
                        # TODO sum volumes or same prices
                        if profit - fees > 0:
                            our_bid.append(trade(ask.value,
                                                 bid.volume, typ=trade.ASK))
                            log.debug('appending to our_bid %s', our_bid[-1])
                            our_ask.append(trade(bid.value,
                                                 bid.volume, typ=trade.BID))
                            log.debug('appending to our_ask %s', our_ask[-1])
                            log.debug('removing %s', bid)
                            bid_depth.remove(bid)
                            res['profitable'] = True
                        else:
                            done = True
                        # continue checking next bid
                else:
                    break

        # sanity check
        if res['profitable']:
            res['asks'] = our_ask
            res['bids'] = our_bid
            res['total_profit'] = total_profit
            #assert(len(our_ask) > 0 and len(our_bid) > 0)
            ask_volume = 0.0
            ask_price_avg = 0.0
            bid_volume = 0.0
            bid_price_avg = 0.0
            for i in our_ask:
                ask_volume += i.volume
                ask_price_avg += i.value * i.volume
            for i in our_bid:
                bid_volume += i.volume
                bid_price_avg += i.value * i.volume
            if ask_price_avg < bid_price_avg:
                log.error("DEPTH ERROR: our_ask_price: %f, our_bid_price: %f",
                          ask_price_avg, bid_price_avg)
                res['error'] = "average ask price is not larger than bid price"
            if ask_volume != bid_volume:
                log.error("DEPTH ERROR: ask_volume: %f, bid_volume: %f",
                          ask_volume, bid_volume)
                res['error'] = "ask and bid volume not equivalent"
            if not total_profit > 0:
                log.error("DEPTH ERROR: total_profit is negative")
                res['error'] = "total profit is negative"

        return res

#    @staticmethod
#    #def spread(api1, api2, pair):
#    def spread(depth1, depth2, fees1=0.02, fees2=0.02):
#
#        """
#        get price spread across two markets
#        Input:
#            depth1    market1 depth
#            depth2    market2 depth
#            fees1     market1 fees
#            fees2     market2 fees
#        """
#
#        log.debug('Calculating spread between: %s and %s',
#                  depth1, depth2)
#
#        r = {}
#
#        mina1 = depth1.get_min_ask()
#        maxb1 = depth1.get_max_bid()
#        log.debug('Min Ask 1: %s', mina1)
#        log.debug('Max Bid 1: %s', maxb1)
#
#        mina2 = depth2.get_min_ask()
#        maxb2 = depth2.get_max_bid()
#        log.debug('Min Ask 2: %s', mina2)
#        log.debug('Max Bid 2: %s', maxb2)
#
#        # mininum sell price (ask) on api1 is lower than maximum buy price
#        # (bid) on api2
#        # => buy from 1 all lower priced asks than maximum bid on 2
#        # => sell on 2 all higher priced bids than minimum ask on 1
#        if mina1 < maxb2:
#            #print('buy from api1 sell api2')
#            trades = {
#                #'buy_api': api1,
#                #'sel_api': api2,
#                'direction': 1,
#                'we_buy': depth1.get_asks_lower(maxb2),
#                'we_sell': depth2.get_bids_higher(mina1),
#                'max_bid': maxb2,
#                'min_ask': mina1,
#            }
#            sell_fees = fees2
#            buy_fees = fees1
#        elif mina2 < maxb1:
#            #print('buy from api2 sell api1')
#            trades = {
#                #'buy_api': api2,
#                #'sel_api': api1,
#                'direction': -1,
#                'we_buy': depth2.get_asks_lower(maxb1),
#                'we_sell': depth1.get_bids_higher(mina2),
#                'max_bid': maxb1,
#                'min_ask': mina2,
#            }
#            sell_fees = fees1
#            buy_fees = fees2
#        else:
#            r['profitable'] = False
#            return r
#
#        log.debug('BUY: %s', trades['we_buy'])
#        log.debug('SELL: %s', trades['we_sell'])
#
#        volume_to_sell = sum(
#            map(lambda t: t.volume, trades['we_sell']))
#        volume_to_buy = sum(
#            map(lambda t: t.volume, trades['we_buy']))
#        volume_to_trade = min(volume_to_sell, volume_to_buy)
#
#        weighted_value_buy = depth1.get_weighted_price(
#            trades['we_buy'], volume_to_trade)
#
#        weighted_value_sell = depth1.get_weighted_price(
#            reversed(trades['we_sell']), volume_to_trade)
#
#        log.debug('weighted_value_buy %f * vol %f = price %f' % (
#            weighted_value_buy, volume_to_trade,
#            weighted_value_buy * volume_to_trade))
#        log.debug('weighted_value_sell %f * vol %f = price %f' % (
#            weighted_value_sell, volume_to_trade,
#            weighted_value_sell * volume_to_trade))
#
#        order_buy = trade(
#            value=trades['max_bid'].value,
#            volume=volume_to_trade,
#            typ=trade.BID
#        )
#
#        #log.debug('BUY ORDER (%s) --> %s', trades['buy_api'], order_buy)
#
#        orders_sell = []
#        vol = volume_to_trade
#        for bid in reversed(trades['we_sell']):
#            if vol < bid.volume:
#                bid.volume = vol
#            order_sell = trade(
#                value=bid.value,
#                volume=bid.volume,
#                typ=trade.ASK
#            )
#            orders_sell.append(order_sell)
#            vol -= bid.volume
#            #log.debug('SEL ORDER (%s) --> %s', trades['sel_api'], order_sell)
#            if vol <= 0.0:
#                break
#
#        r['profit_gross'] = (weighted_value_sell - weighted_value_buy) * \
#            volume_to_trade
#
#        fees = weighted_value_sell * volume_to_trade * sell_fees
#        fees += weighted_value_buy * volume_to_trade * buy_fees
#
#        r['profit_net'] = r['profit_gross'] - fees
#        r['profitable'] = r['profit_net'] > 0.0
#
#        r['order_buy'] = order_buy
#        #r['api_buy'] = trades['buy_api']
#        r['orders_sell'] = orders_sell
#        #r['api_sell'] = trades['sel_api']
#
#        log.debug('Spread result %s', r)
#
#        if r['profitable']:
#            log.info(' -----> PROFIT: %s', r)
#
#        return (r)

    def __repr__(self):
        r = ''
        for ask in self.asks:
            r += '%s\n' % ask

        for bid in self.bids:
            r += '%s\n' % bid

        return r
