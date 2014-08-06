#!/usr/bin/python

import requests
import json
import time
import hmac
import hashlib
import urllib
import random
from token_bucket import TokenBucket

import logging
log = logging.getLogger('cryptsy')
LOG_LEVEL = logging.DEBUG
log.setLevel(LOG_LEVEL)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

# 10 requests per second ????
RATE = 10.0


coin_symbols = {
    'litecoin': 'LTC',
}


class api(object):
    def __init__(self,
                 key='',
                 secret=''):
        self.url = 'https://api.cryptsy.com/api'
        self.key = key
        self.secret = secret
        self.markets = None
        self.rate_limiter = TokenBucket(RATE)
        random.seed(time.time())

    def __query(self, method, params={}):
        req = params
        req['method'] = method
        req['nonce'] = int(time.time())
        data = urllib.urlencode(req)
        sign = hmac.new(self.secret, data, hashlib.sha512).hexdigest()
        headers = {
            'Sign': sign,
            'Key': self.key
        }

        while not self.rate_limiter.may_i():
            time.sleep(random.uniform(0.5, 3.0))

        r = requests.post(self.url, data=data, headers=headers)
        if r.status_code == 200:
            c = json.loads(r.content)
            if c['success'] == u'1':
                if method == 'createorder':
                    return c['orderid']
                return c['return']
            else:
                log.error('Error calling %s(%s) on %s', method, params, self.url)
                log.error(c)
                log.error(c['error'])
        else:
            log.error('Error calling %s(%s) on %s', method, params, self.url)
        return None

    def getinfo(self):
        """
        Outputs:
            balances_available  Array of currencies and the balances availalbe for each
            balances_hold       Array of currencies and the amounts currently on hold for open orders
            servertimestamp     Current server timestamp
            servertimezone      Current timezone for the server
            serverdatetime      Current date/time on the server
            openordercount      Count of open orders on your account
        """
        return self.__query('getinfo')

    def getmarkets(self):
        """
        Outputs: Array of Active Markets
            marketid                Integer value representing a market
            label                   Name for this market, for example: AMC/BTC
            primary_currency_code   Primary currency code, for example: AMC
            primary_currency_name   Primary currency name, for example: AmericanCoin
            secondary_currency_code Secondary currency code, for example: BTC
            secondary_currency_name Secondary currency name, for example: BitCoin
            current_volume          24 hour trading volume in this market
            last_trade              Last trade price for this market
            high_trade              24 hour highest trade price in this market
            low_trade               24 hour lowest trade price in this market
            created                 Datetime (EST) the market was created
        """
        return self.__query('getmarkets')

    def getwalletstatus(self):
        """
        Outputs: Array of Wallet Statuses
            currencyid      Integer value representing a currency
            name            Name for this currency, for example: Bitcoin
            code            Currency code, for example: BTC
            blockcount      Blockcount of currency hot wallet as of lastupdate time
            difficulty      Difficulty of currency hot wallet as of lastupdate time
            version         Version of currency hotwallet as of lastupdate time
            peercount       Connected peers of currency hot wallet as of lastupdate time
            hashrate        Network hashrate of currency hot wallet as of lastupdate time
            gitrepo         Git Repo URL for this currency
            withdrawalfee   Fee charged for withdrawals of this currency
            lastupdate      Datetime (EST) the hot wallet information was last updated
        """
        return self.__query('getwalletstatus')

    def mytransactions(self):
        """
        Outputs: Array of Deposits and Withdrawals on your account
            currency    Name of currency account
            timestamp   The timestamp the activity posted
            datetime    The datetime the activity posted
            timezone    Server timezone
            type        Type of activity. (Deposit / Withdrawal)
            address     Address to which the deposit posted or Withdrawal was sent
            amount      Amount of transaction (Not including any fees)
            fee Fee     (If any) Charged for this Transaction (Generally only on Withdrawals)
            trxid       Network Transaction ID (If available)
        """
        return self.__query('mytransactions')

    def markettrades(self, marketid):
        """
        Inputs:
            marketid            Market ID for which you are querying

        Outputs: Array of last 1000 Trades for this Market, in Date Decending Order
            tradeid             A unique ID for the trade
            datetime            Server datetime trade occurred
            tradeprice          The price the trade occurred at
            quantity            Quantity traded
            total               Total value of trade (tradeprice * quantity)
            initiate_ordertype  The type of order which initiated this trade
        """
        return self.__query('markettrades', params={'marketid': marketid})

    def marketorders(self, marketid):
        """
        Inputs:
            marketid    Market ID for which you are querying


        Outputs: 2 Arrays. First array is sellorders listing current open sell orders ordered price ascending.
            Second array is buyorders listing current open buy orders ordered price descending.
            sellprice   If a sell order, price which order is selling at
            buyprice    If a buy order, price the order is buying at
            quantity    Quantity on order
            total       Total value of order (price * quantity)
        """
        return self.__query('marketorders', params={'marketid': marketid})

    def mytrades(self, marketid, limit=200):
        """

        Inputs:
            marketid    Market ID for which you are querying
            limit       (optional) Limit the number of results. Default: 200

        Outputs: Array your Trades for this Market, in Date Decending Order
            tradeid             An integer identifier for this trade
            tradetype           Type of trade (Buy/Sell)
            datetime            Server datetime trade occurred
            tradeprice          The price the trade occurred at
            quantity            Quantity traded
            total               Total value of trade (tradeprice * quantity) - Does not include fees
            fee                 Fee Charged for this Trade
            initiate_ordertype  The type of order which initiated this trade
            order_id            Original order id this trade was executed against
        """
        return self.__query('marketorders', params={'marketid': marketid, 'limit': limit})

    def allmytrades(self, startdate, enddate):
        """

        Inputs:
            startdate   (optional) Starting date for query (format: yyyy-mm-dd)
            enddate     (optional) Ending date for query (format: yyyy-mm-dd)

        Outputs: Array your Trades for all Markets, in Date Decending Order
            tradeid             An integer identifier for this trade
            tradetype           Type of trade (Buy/Sell)
            datetime            Server datetime trade occurred
            marketid            The market in which the trade occurred
            tradeprice          The price the trade occurred at
            quantity            Quantity traded
            total               Total value of trade (tradeprice * quantity) - Does not include fees
            fee                 Fee Charged for this Trade
            initiate_ordertype  The type of order which initiated this trade
            order_id            Original order id this trade was executed against
        """
        return self.__query('allmytrades',
                            params={'startdate': startdate, 'enddate': enddate})

    def myorders(self, marketid):
        """
        Inputs:
            marketid    Market ID for which you are querying

        Outputs: Array of your orders for this market listing your current open sell and buy orders.
            orderid         Order ID for this order
            created         Datetime the order was created
            ordertype       Type of order (Buy/Sell)
            price           The price per unit for this order
            quantity        Quantity remaining for this order
            total           Total value of order (price * quantity)
            orig_quantity   Original Total Order Quantity
        """
        return self.__query('myorders', params={'marketid': marketid})

    def depth(self, marketid):
        """
        Inputs:
            marketid    Market ID for which you are querying

        Outputs: Array of buy and sell orders on the market representing market depth.
            Output Format is:
            array(
              'sell'=>array(
                array(price,quantity),
                array(price,quantity),
                ....
              ),
              'buy'=>array(
                array(price,quantity),
                array(price,quantity),
                ....
              )
            )
        """
        return self.__query('depth', params={'marketid': marketid})

    def allmyorders(self):
        """
        Outputs: Array of all open orders for your account.
        orderid         Order ID for this order
        marketid        The Market ID this order was created for
        created         Datetime the order was created
        ordertype       Type of order (Buy/Sell)
        price           The price per unit for this order
        quantity        Quantity remaining for this order
        total           Total value of order (price * quantity)
        orig_quantity   Original Total Order Quantity
        """
        return self.__query('allmyorders')

    def createorder(self, marketid, ordertype, quantity, price):
        """
        Inputs:
            marketid    Market ID for which you are creating an order for
            ordertype   Order type you are creating (Buy/Sell)
            quantity    Amount of units you are buying/selling in this order
            price       Price per unit you are buying/selling at

        Outputs:
            orderid     If successful, the Order ID for the order which was created
        """
        return self.__query('createorder',
                            params={
                                'marketid': marketid,
                                'ordertype': ordertype,
                                'quantity': quantity,
                                'price': price
                            }
                            )

    def cancelorder(self, orderid):
        """
        Inputs:
            orderid Order ID for which you would like to cancel
        """
        return self.__query('cancelorder', params={'orderid': orderid})

    def cancelmarketorders(self, marketid):
        """
        Inputs:
            marketid    Market ID for which you would like to cancel all open orders

        Outputs:
            return      Array for return information on each order cancelled
        """
        return self.__query('cancelmarketorders', params={'marketid': marketid})

    def cancelallorders(self):
        """
        Inputs: N/A

        Outputs:
            return  Array for return information on each order cancelled
        """
        return self.__query('cancelallorders')

    def calculatefees(self, ordertype, quantity, price):
        """
        Inputs:
            ordertype   Order type you are calculating for (Buy/Sell)
            quantity    Amount of units you are buying/selling
            price       Price per unit you are buying/selling at

        Outputs:
            fee         The that would be charged for provided inputs
            net         The net total with fees
        """
        return self.__query('calculatefees',
                            params={'ordertype': ordertype,
                                    'quantity': quantity,
                                    'price': price
                                    })

    def generatenewaddress(self, currencyid, currencycode):
        """
        Inputs: (either currencyid OR currencycode required - you do not have to supply both)
            currencyid      Currency ID for the coin you want to generate a new address for (ie. 3 = BitCoin)
            currencycode    Currency Code for the coin you want to generate a new address for (ie. BTC = BitCoin)

        Outputs:
            address         The new generated address
        """
        return self.__query('generatewalletaddress',
                            params={'currencyid': currencyid,
                                    'currencycode': currencycode,
                                    })

    def mytransfers(self):
        """
        Inputs: n/a

        Outputs: Array of all transfers into/out of your account sorted by requested datetime descending.
            currency            Currency being transfered
            request_timestamp   Datetime the transfer was requested/initiated
            processed           Indicator if transfer has been processed (1) or not (0)
            processed_timestamp Datetime of processed transfer
            from                Username sending transfer
            to                  Username receiving transfer
            quantity            Quantity being transfered
            direction           Indicates if transfer is incoming or outgoing (in/out)
        """
        return self.__query('mytransfers')

    def makewithdrawal(self, address, amount):
        """
        Inputs:
            address Pre-approved Address for which you are withdrawing to (Set up these addresses on Settings page)
            amount  Amount you are withdrawing. Supports up to 8 decimal places.

        Outputs:
            Either successful or error. If error, gives reason for error.
        """
        return self.__query('makewithdrawal', params={'address': address, 'amount': amount})

    def getmydepositaddresses(self):
        """
        Inputs: n/a

        Outputs:
            return  Array for return information on each order cancelled ("coincode" => "despositaddress")
        """
        return self.__query('getmydepositaddresses')

    def getorderstatus(self, orderid):
        """
        Inputs:
            orderid     Order ID for which you are querying

        Outputs:

            tradeinfo is a list of all the trades that have occured in your order.
            Where orderinfo shows realtime status of the order.
            Orderinfo contains the 'active'; a boolean object showing if the order is still open.
            Orderinfo also contains 'remainqty' which shows the quantity left in your order.

            tradeinfo   A list of all trades that have occuried in your order.
            orderinfo   Information regarding status of the order. Contains 'active' and 'remainqty' keys.
        """
        return self.__query('getorderstatus', params={'orderid': orderid})

    def ex_coin_rev(self, buy_symbol, sell_symbol, sell_volume):
        orderids = []
        log.info('selling %.8f %s for %s',
                 sell_volume, sell_symbol, buy_symbol)
        if not self.markets:
            self.markets = self.getmarkets()

        market_id = ''
        for market in self.markets:
            if market['primary_currency_code'] == buy_symbol and \
                    market['secondary_currency_code'] == sell_symbol:
                log.info(market)
                market_id = market['marketid']
                break
        assert(market_id)

        # get buy orders for ltc
        depth = self.depth(market_id)
        bought = 0.0
        remaining_sell_volume = sell_volume
        for order in depth['sell']:
            log.debug(order)
            order_volume_to_sell = float(order[1])
            order_price_per_coin = float(order[0])
            total_price = order_volume_to_sell * order_price_per_coin
            log.debug('Order %.8f %s for %.8f per coin',
                      order_volume_to_sell, sell_symbol, order_price_per_coin)
            if remaining_sell_volume < total_price:
                order_volume_to_sell = remaining_sell_volume / order_price_per_coin
            #fees = float(self.calculatefees('Sell', order_volume_to_sell, order_price_per_coin)['fee'])
            # TODO
            fees = order_volume_to_sell * order_price_per_coin * 0.002
            log.debug('We buy %.8f %s for %.8f per coin (total btc %0.8f)',
                      order_volume_to_sell, buy_symbol, order_price_per_coin,
                      order_volume_to_sell * order_price_per_coin)
            orderid = self.createorder(market_id, 'Buy', order_volume_to_sell, order_price_per_coin)
            if not orderid:
                log.error('could not set order')
            else:
                orderids.append(orderid)
            bought += order_volume_to_sell - fees
            remaining_sell_volume -= total_price
            if remaining_sell_volume <= 0:
                break
        #return (bought, remaining_sell_volume)
        return orderids

    def ex_coin(self, buy_symbol, sell_symbol, sell_volume):
        orderids = []
        log.info('selling %.8f %s for %s',
                 sell_volume, sell_symbol, buy_symbol)
        if not self.markets:
            self.markets = self.getmarkets()

        market_id = ''
        for market in self.markets:
            if market['primary_currency_code'] == sell_symbol and \
                    market['secondary_currency_code'] == buy_symbol:
                log.info(market)
                market_id = market['marketid']
                break
        assert(market_id)

        # get buy orders for ltc
        depth = self.depth(market_id)
        bought = 0.0
        remaining_sell_volume = sell_volume
        for order in depth['buy']:
            log.debug(order)
            order_volume_to_sell = float(order[1])
            order_price_per_coin = float(order[0])
            log.debug('Order %f %s for %f per coin',
                      order_volume_to_sell, sell_symbol, order_price_per_coin)
            if remaining_sell_volume < order_volume_to_sell:
                order_volume_to_sell = remaining_sell_volume
            #fees = float(self.calculatefees('Sell', order_volume_to_sell, order_price_per_coin)['fee'])
            # TODO
            fees = order_volume_to_sell * order_price_per_coin * 0.002
            orderid = self.createorder(market_id, 'Sell', order_volume_to_sell, order_price_per_coin)
            if not orderid:
                log.error('could not set order')
            else:
                orderids.append(orderid)

            bought += order_volume_to_sell * order_price_per_coin - fees
            remaining_sell_volume -= order_volume_to_sell
            if remaining_sell_volume <= 0:
                break
        #return (bought, remaining_sell_volume)
        return orderids

if __name__ == '__main__':

    import logging
    LOG_FILENAME = '/tmp/payout.log'
    LOG_LEVEL = logging.DEBUG
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)d %(levelname)s' +
                        '%(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")
    log = logging.getLogger('dbi_redis')
    log.setLevel(LOG_LEVEL)

    key = 'f378dcc37bb33a5589bf22dbc011eb075c87a14b'
    secret = '9a46727fdc6b480ff2ff7ed9813f0d822997d4e42c2848d21c899e236b9d707abff0d59fac2d259e'
    c = api(key, secret)
    #from pprint import pprint
    #pprint(c.getinfo())
    #pprint(c.getmarkets())
    bought, remaining_sell_volume = c.ex_coin('BTC', 'LTC', 100.0)
    print 'Bought %f btc (%f remaining)' % (bought, remaining_sell_volume)
    #print '-' * 80
    #pprint(c.getmarkets())
    #print '-' * 80
    #pprint(c.getwalletstatus())
    #print '-' * 80
    #pprint(c.mytransactions())
    #print '-' * 80
    #print repr(c.getmarkets())
