#!/usr/bin/env python3
import json
import configparser
#from modules.exsimuapi import datasets


class API:
    __api_key = ''
    __api_secret = ''
    __nonce_v = 1
    __wait_for_nonce = False
#    __txid = 0
#    __data_set = {}
#    __active_orders = {}
#    __closed_orders = {}
#    __balance = {}

    def __init__(self, data):
        self.__data_set = data
        fname = 'modules/exsimuapi/' + self.__data_set + '.dat'
        with open(fname) as f:
            self.__depth_data = json.loads(f.read())
        self.__balance = {}
        self.__active_orders = {}
        self.__closed_orders = {}
        self.__config = configparser.ConfigParser()
        self.__configname = 'modules/exsimuapi/' + self.__data_set + '.ini'
        try:
            self.__config.read(self.__configname)
            for cur in self.__config['balance']:
                self.__balance[cur] = float(self.__config['balance'][cur])
            self.__orderid = int(self.__config['orders']['orderid'])
            self.__active_orders = dict(self.__config['active_orders'])
            self.__closed_orders = dict(self.__config['closed_orders'])
        except:
            self.__orderid = 0
            self.__balance['btc'] = float(0.95)
            self.__balance['eur'] = float(2000)
            self.__balance['usd'] = float(59)
            self.__config['balance'] = self.__balance
            pass

    def save_config(self):
        self.__config['balance'] = self.__balance
        self.__config['active_orders'] = self.__active_orders
        self.__config['closed_orders'] = self.__closed_orders
        self.__config['orders'] = {'orderid': self.__orderid}
        with open(self.__configname, 'w') as f:
            self.__config.write(f)

    def modify_balance(self, cur, amount):
        self.__balance[cur] = float(amount)
        self.save_config()

    # return depth
    def get_depth(self, pair):
        return self.__depth_data

    # return active orders
    def get_active_orders(self):
        return self.__active_orders

    # return balance
    def get_balance(self):
        return self.__balance

    # execute orders
    def execute_orders(self, **order):
        price = float(order['price'])
        if order['order'] == 'buy':
            depth = self.__depth_data['asks']
            trades = reversed(list(
                filter(lambda t: float(t[0]) <= price, depth)))
        elif order['order'] == 'sell':
            depth = self.__depth_data['bids']
            trades = list(filter(lambda t: float(t[0]) >= price, depth))

        # TODO average price
        order['executed_volume'] = 0
        vol = order['volume']
        price_avg = 0
        for trade in trades:
            if vol > trade[1]:
                vol -= trade[1]
                print('depth item consumed', trade)
                price_avg += trade[0] * trade[1]
                depth.remove(trade)
                order['executed_volume'] += trade[1]
                order['state'] = 'partial'
            else:
                print('depth item reduced by %f %s' %
                      (vol, repr(depth[depth.index(trade)])))
                price_avg += trade[0] * vol
                depth[depth.index(trade)][1] -= vol
                vol = 0
                order['executed_volume'] = order['volume']
                order['state'] = 'closed'
                break
        price_avg /= order['executed_volume']
        order['executed_price_avg'] = price_avg

        return order

    # add order to list and deduct funds / btc
    def add_order(self, pair, order, price, vol):
        if pair == 'btc_eur':
            cur = 'eur'
        elif pair == 'btc_usd':
            cur = 'usd'
        else:
            raise Exception('pair not implemented')
        if order == 'buy':
            if float(price) * float(vol) > self.__balance[cur]:
                raise Exception('EOrder:Insufficient funds')
            else:
                self.__balance[cur] -= float(price) * float(vol)
        elif order == 'sell':
            if float(vol) > self.__balance['btc']:
                raise Exception('EOrder:Insufficient volume')
            else:
                self.__balance['btc'] -= float(vol)
        order_id = 'tx_' + str(self.__orderid)
        new_order = {
            'pair': str(pair),
            'order': str(order),
            'price': float(price),
            'volume': float(vol),
            'state': 'open',
            #'txid': order_id
        }
        self.__orderid += 1

        new_order = self.execute_orders(**new_order)
        if new_order['state'] == 'open' or new_order['state'] == 'partial':
            self.__active_orders[order_id] = new_order
        elif new_order['state'] == 'closed':
            self.__closed_orders[order_id] = new_order

        if new_order['state'] == 'partial' or new_order['state'] == 'closed':
            if order == 'buy':
                self.__balance['btc'] += new_order['executed_volume']
                self.__balance[cur] += float(price) * float(vol)
                self.__balance[cur] -= new_order['executed_volume'] * \
                    new_order['executed_price_avg']
            elif order == 'sell':
                self.__balance[cur] += float(price) * \
                    new_order['executed_volume']
            self.save_config()

        return new_order

    # delete order from dict and restore funds / btc
    def cancel_order(self, order_id):
        order = {}
        if order_id in self.__active_orders.keys():
            order = self.__active_orders[order_id]
            if order['pair'] == 'btc_usd':
                cur = 'usd'
            elif order['pair'] == 'btc_eur':
                cur = 'eur'
            else:
                raise Exception('pair not implemented')
            if order['order'] == 'buy':
                self.__balance[cur] += float(order['price'])
            elif order['order'] == 'sell':
                self.__balance['btc'] += float(order['volume'])
            else:
                raise Exception('something went utterly wrong')
            del self.__active_orders[order_id]
        else:
            raise Exception('order id does not exist')
        return order
