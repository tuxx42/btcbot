#!/usr/bin/env python3
import modules.exsimuapi
import time
from exapi import ExAPI
from depth import depth
import logging
log = logging.getLogger(__name__)

#    pair = "btc_usd"


class exsimu(ExAPI):

    def __init__(self, data, name='exsimu'):
        self.api = modules.exsimuapi.API(data)
        self.name = name
        self.curdepth = {}

    def fees(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        if kwargs['pair'] == 'btc_eur':
            return self.api.fees()
        else:
            return Exception('cannot get fees')

    def get_balance(self, dummy=None):
        try:
            self.balance = self.api.get_balance()
            return self.balance
        except Exception as e:
            print(e)
            raise Exception('cannot get balance')

    def add_order(self, order, price, vol, ordertype='limit', pair='btc_eur'):
        print('executing trade order %s: %s, value: %f, volume: %f, type: %s' %
              (self.name, order, price, vol, ordertype))
        s = self.api.add_order(pair=pair,
                               order=order,
                               price=price,
                               vol=vol)
        return s

    def active_orders(self):
        return self.api.get_active_orders()

    def modify_balance(self, **kwargs):
        for cur in kwargs.keys():
            return self.api.modify_balance(cur, kwargs[cur])

    def trade_history(self):
        pass

    def cancel_order(self, orderid):
        return self.api.cancel_order(orderid)

    def depth(self, pair='btc_eur'):
        #kwargs.setdefault('pair', 'btc_eur')
        try:
            s = self.api.get_depth({'pair': pair})
        except Exception as e:
            print(e)
        d = depth(**s)
        self.curdepth[pair] = [d, time.time()]
        return d
