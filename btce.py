#!/usr/bin/env python3
import modules.btceapi
import time
from exapi import ExAPI
from depth import depth

#    pair = "btc_usd"


class btce(ExAPI):
    curdepth = {}
    name = 'btce'

    def __init__(self, passwd=None):
        self.api = modules.btceapi.API(
            'XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX',
            'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

    def get_fees(self, **kwargs):
        return 0.002
        kwargs.setdefault('pair', 'btc_eur')
        s = self.api.get_param(kwargs['pair'], 'fee')
        try:
            fee = s['trade']
            return fee
        except:
            return Exception('unable to get pair?')

    def get_balance(self, dummy=None):
        balance = {}
        try:
            result = self.api.getInfo()['return']['funds']
            for s in ['btc', 'eur']:
                balance[s] = result[s]
            return balance
        except Exception as e:
            print(e)

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_depth(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        try:
            s = self.api.get_param(kwargs['pair'], 'depth')
        except Exception as e:
            print(e)
        d = depth(**s)
        btce.curdepth[kwargs['pair']] = [d, time.time()]
        return d
