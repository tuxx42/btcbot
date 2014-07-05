#!/usr/bin/env python3
from exapi import ExAPI
import modules.krakenex
import time
from depth import depth

import logging
log = logging.getLogger(__name__)


class kraken(ExAPI):
    PADDING = '{'
    curdepth = {}
    pairs = {}
    name = 'kraken'
    pairs['btc_eur'] = 'XXBTZEUR'
    pairs['btc'] = 'XXBT'
    pairs['eur'] = 'ZEUR'

    def __init__(self, key_mgmt):
        self.k = modules.krakenex.API(
            key=key_mgmt.key,
            secret=key_mgmt.secret,
        )

    def fees(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        fees = {}
        fees['btc_eur'] = 0.002
        fees['btc_usd'] = 0.002
        try:
            return fees[kwargs['pair']]
        except KeyError:
            raise Exception('invalid pair')

    def balance(self, dummy=None):
        s = self.k.query_private('Balance')
        if s['error']:
            print ("an error occured while getting the account balance: %s" %
                   s['error'])
            raise Exception('could not query')
        else:
            balance = {}
            balance['btc'] = float(s['result']['XXBT'])
            balance['eur'] = float(s['result']['ZEUR'])
            return balance

    def add_order(self, order, price, vol, ordertype='limit', pair='btc_eur'):
        return 'blocked'
        getpair = kraken.pairs[pair]
        try:
            res = self.k.query_private('AddOrder',
                                       {'pair': getpair,
                                        'type': order,
                                        'ordertype': ordertype,
                                        'price': price,
                                        'volume': vol,
                                        })
        except Exception as e:
            print(e)
            raise Exception('could not issue order')
        if res['error']:
            raise Exception(res['error'])
        else:
            return res

    def trades(self, **kwargs):
        try:
            s = self.k.query_public('Trades', kwargs)
        except:
            print ("unable to get trades")
            raise Exception
        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception
        print(s['result'])

    def active_orders(self):
        res = self.k.query_private('OpenOrders')
        return res

    def closed_orders(self):
        res = self.k.query_private('ClosedOrders')
        return res

    def query_order(self, order_id):
        res = self.k.query_private('QueryOrders',
                                   {'txid': order_id})
        return res

    def cancel_order(self, orderid):
        res = self.k.query_private('CancelOrder',
                                   {'txid': orderid})
        return res

    def depth(self, pair='btc_eur', count=10):
        try:
            s = self.k.query_public('Depth', {'pair': kraken.pairs[pair],
                                              'count': count})
        except Exception as e:
            log.exception(e)
            raise

        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception(s['error'])

        d = [depth(**v) for k, v in s['result'].items()][0]
        self.curdepth[pair] = [d, time.time()]
        return d
