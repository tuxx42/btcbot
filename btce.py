#!/usr/bin/env python3
import modules.btceapi
import time
from exapi import ExAPI
from depth import depth

#    pair = "btc_usd"


class btce(ExAPI):
    current_depth = []

    def __init__(self, passwd=None):
        self.api = modules.btceapi.API(
            'XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX',
            'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

    def decipher_key(self, blubb=None):
        pass

    def get_balance(self, dummy=None):
        balance = {}
        try:
            result = self.api.getInfo()['return']['funds']
            for s in ['btc', 'eur']:
                balance[s] = result[s]
            return balance
        except Exception as e:
            print(e)
        pass

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_min_bid(self):
        try:
            return btce.current_depth[-1][0].get_min_bid()
        except Exception as e:
            print(e)

    def get_max_ask(self):
        return btce.current_depth[-1][0].get_max_bid()

    def get_depth(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        try:
            s = self.api.get_param(kwargs['pair'], 'depth')
        except Exception as e:
            print(e)
        d = depth(**s)
        btce.current_depth.append([d, time.time()])
        return d
