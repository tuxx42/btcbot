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
        print ('reached')
        print (modules.btceapi.getTradeFee('btc_eur', self.connection))
        print (modules.btceapi.getInfo(self.connection))
        pass

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_depth(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        try:
            asks, bids = self.api.get_param(kwargs['pair'], 'Depth')
            print(asks, bids)
        except Exception as e:
            print(e)
        #d = depth(asks=asks, bids=bids)
        #btce.current_depth.append([d, time.time()])
        #return d
