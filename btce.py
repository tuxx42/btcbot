#!/usr/bin/env python3
import modules.btceapi
import time
from exapi import ExAPI
from depth import depth

#    pair = "btc_usd"


class btce(ExAPI):
    current_depth = []
    def __init__(self, passwd=None):
        pass

    def decipher_key(self, blubb=None):
        pass

    def get_balance(self, dummy=None):
        pass

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_depth(self, **kwargs):
        pair = "btc_eur"
        try:
            pair = kwargs['pairs']
        except KeyError:
            pass
        try:
            asks, bids = modules.btceapi.getDepth(pair)
        except Exception as e:
            print(e)
        # {'XXBTZEUR': {'bids': [['427.35800', '0.100', 1403904879]], 'asks':
        # [['427.96708', '0.117', 1403905459]]}}
        #depth = {pair: {'bits': [bids], 'asks': [asks]}}
        d = depth(asks=asks, bids=bids)
        btce.current_depth.append([d, time.time()])
        return d
