#!/usr/bin/env python3
import modules.btceapi
import time
from exapi import ExAPI
from depth import depth

import logging
log = logging.getLogger(__name__)

#    pair = "btc_usd"


class btce(ExAPI):
    curdepth = {}
    #issued_orders = []
    name = 'btce'

    def __init__(self, key_mgmt):
        self.api = modules.btceapi.API(
            key_mgmt.key,
            key_mgmt.secret)

    def fees(self, **kwargs):
        return 0.002
        kwargs.setdefault('pair', 'btc_eur')
        s = self.api.get_param(kwargs['pair'], 'fee')
        try:
            fee = s['trade']
            return fee
        except:
            return Exception('unable to get pair?')

    def balance(self, dummy=None):
        balance = {}
        try:
            result = self.api.getInfo()['return']['funds']
            for s in ['btc', 'eur']:
                balance[s] = result[s]
            return balance
        except Exception as e:
            print(e)

    def add_order(self, order, price, vol, ordertype='limit', pair='btc_eur'):
        try:
            result = self.api.Trade(tpair=pair,
                                    ttype=order,
                                    trate=price,
                                    tamount=vol)
            return result
        except Exception as e:
            print(e)
            raise Exception('could not issue order')
        if result['success']:
            #self.issued_orders.append(result['return']['order_id'])
            return result['return']

    def trades(self, **kwargs):
        pass

    def depth(self, pair='btc_eur', count=20):
        try:
            s = self.api.get_param(pair, 'depth')
        except Exception as e:
            log.exception(e)
            raise
        d = depth(**s)
        d.asks = d.asks[:count]
        d.bids = d.bids[-count:]
        btce.curdepth[pair] = [d, time.time()]
        return d
