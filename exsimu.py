#!/usr/bin/env python3
import modules.exsimuapi
import time
from exapi import ExAPI
from depth import depth

#    pair = "btc_usd"


class exsimu(ExAPI):

    def __init__(self, data, name='exsimu'):
        self.api = modules.exsimuapi.API(data)
        self.name = name
        self.curdepth = {}

    def get_fees(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        if kwargs['pair'] == 'btc_eur':
            return 0.2
        else:
            return Exception('pair?')

    def get_balance(self, dummy=None):
        try:
            return self.api.get_balance()
        except Exception as e:
            print(e)

    def add_order(self, order, price, vol):
        print('adding order(%s), price(%s), vol(%s)' % (order, price, vol))

    def get_trades(self, **kwargs):
        pass

    def print_depth(self, **kwargs):
        print(self.curdepth)

    def get_depth(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        try:
            s = self.api.get_depth(kwargs)
        except Exception as e:
            print(e)
        d = depth(**s)
        self.curdepth[kwargs['pair']] = [d, time.time()]
        return d
