#!/usr/bin/env python3
from exapi import ExAPI
import modules.krakenex
import time
from depth import depth
from global_vars import gv

import logging
log = logging.getLogger(__name__)


class kraken(ExAPI):
    PADDING = '{'
    curdepth = {}
    pairs = {}
    name = 'kraken'
    pairs['btc_eur'] = 'XXBTZEUR'
    pairs['btc_usd'] = 'XXBTZUSD'
    pairs['btc'] = 'XXBT'
    pairs['eur'] = 'ZEUR'

    def __init__(self, key_mgmt, name=None):
        self.api = modules.krakenex.API(
            key=key_mgmt.key,
            secret=key_mgmt.secret,
        )
        self.balance = self.get_balance()
        self.fee_table = {}
        if name:
            self.name = name
        else:
            self.name = "kraken"

    def fees(self, pair="btc_eur"):
        if not pair in self.fee_table.keys():
            self.update_fees(pair)
        return self.fee_table[pair]

    def update_fees(self, pair='btc_eur'):
        try:
            res = self.api.query_private('TradeVolume',
                                         {'pair': self.pairs[pair]})
        except Exception as e:
            print(e)
            raise Exception('unable to get fee')
        if res['error']:
            raise Exception(res['error'])
        else:
            res = res['result']['fees']
        try:
            self.fee_table[pair] = float(res[self.pairs[pair]]['fee']) / 100.0
            return self.fee_table[pair]
        except KeyError:
            raise Exception('unable to get fee')

    def get_balance(self):
        s = self.api.query_private('Balance')
        if s['error']:
            print ("an error occured while getting the account balance: %s" %
                   s['error'])
            raise Exception('could not query')
        else:
            balance = {}
            for i in ['btc', 'eur']:
                balance[i] = float(s['result'][self.pairs[i]])
            self.balance = balance
            return self.balance

    def add_order(self, order, price, vol, ordertype='limit', pair='btc_eur'):
        getpair = self.pairs[pair]
        print('executing trade order: %s, value: %f, '
              'volume: %f, type: %s, pair: %s' %
              (order, price, vol, ordertype, getpair))

        return 'blocked'
        try:
            res = self.api.query_private('AddOrder',
                                         {'pair': getpair,
                                          'type': order,
                                          'ordertype': ordertype,
                                          'price': price,
                                          'volume': vol,
                                          })
        except Exception as e:
            log.error('[%s] exception occured %s, %s',
                      self.name, e, res)
            print(e)
            raise Exception('could not issue order')
        if res['error']:
            log.error('[%s] returned erroneous result %s',
                      self.name, res)
            raise Exception(res['error'])
        else:
            log.debug('[%s] trade successful %s',
                      self.name, res)
            return res

    def trades(self, **kwargs):
        try:
            s = self.api.query_public('Trades', kwargs)
        except:
            print ("unable to get trades")
            raise Exception
        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception
        print(s['result'])

    def active_orders(self):
        res = self.api.query_private('OpenOrders')
        return res

    def closed_orders(self):
        res = self.api.query_private('ClosedOrders')
        return res

    def query_order(self, order_id):
        res = self.api.query_private('QueryOrders',
                                     {'txid': order_id})
        return res

    def cancel_order(self, orderid):
        res = self.api.query_private('CancelOrder',
                                     {'txid': orderid})
        return res

    def get_ledgers(self, pair='btc_eur'):
        res = self.api.query_private('TradeVolume', {'pair': self.pairs[pair]})
        print(res)

    def depth(self, pair='btc_eur'):
        if 'depth_count' in gv.keys():
            count = int(gv['depth_count'])
        else:
            count = 20

        try:
            s = self.api.query_public('Depth', {'pair': self.pairs[pair],
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
