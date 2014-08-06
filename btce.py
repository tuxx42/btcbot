#!/usr/bin/env python3
import modules.btceapi
import time
from exapi import ExAPI
from depth import depth
from global_vars import gv
from depth import trade

import logging
log = logging.getLogger(__name__)

#    pair = "btc_usd"


class btce(ExAPI):
    curdepth = {}
    #issued_orders = []
    name = 'btce'
    pairs = {}
    #pairs['ltc_btc'] = 'btc_ltc'

    def __init__(self, key_mgmt, name=None):
        self.api = modules.btceapi.API(
            key_mgmt.key,
            key_mgmt.secret)
        if name:
            self.name = name
        else:
            self.name = "btc-e"

    def fees(self, **kwargs):
        return 0.002
        kwargs.setdefault('pair', 'btc_eur')
        s = self.api.get_param(kwargs['pair'], 'fee')
        try:
            fee = s['trade']
            return fee
        except:
            return Exception('unable to get pair?')

    def get_balance(self):
        balance = {}
        try:
            result = self.api.getInfo()
            if result['success'] == 0:
                return result['error']
            for s in ['btc', 'eur']:
                balance[s] = result['return']['funds'][s]
            self.balance = balance
            return self.balance
        except Exception as e:
            print(e)

    def add_order(self, order, price, vol, ordertype='limit', pair='btc_eur'):
        print('executing trade order: %s, value: %f, volume: %f, type: %s, pair: %s' %
              (order, price, vol, ordertype, pair))
        return 'blocked'
        try:
            print('self.api.Trade(tpair=%s, ttype=%s, trate=%s, tamount=%s' %
                  (pair, order, price, vol))
            res = self.api.Trade(tpair=pair,
                                 ttype=order,
                                 trate=price,
                                 tamount=round(vol, 8))
            log.debug('[%s] trade successful %s', self.name, res)
            return res
        except Exception as e:
            log.debug('[%s] exception occured %s, %s',
                      self.name, e, res)
            print(e)
            raise Exception('could not issue order')

    def trades(self, **kwargs):
        pass

    def depth(self, pair='btc_eur'):
        if 'depth_count' in gv.keys():
            count = int(gv['depth_count'])
        else:
            count = 20
        try:
            if pair == 'btc_ltc':
                pair = 'ltc_btc'
            s = self.api.get_param(pair, 'depth')
        except Exception as e:
            log.exception(e)
            raise Exception('could not get depth')
        d = depth(**s)
        if pair == 'ltc_btc':
            d.asks = list(map(lambda t: trade(1 / t.value, t.volume), d.asks))
            d.bids = list(map(lambda t: trade(1 / t.value, t.volume), d.bids))
        d.asks = d.asks[:count]
        d.bids = d.bids[-count:]
        btce.curdepth[pair] = [d, time.time()]
        return d
