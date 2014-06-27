# Copyright (c) 2013 Alan McIntyre
__version__ = "0.3.0"
from modules.btceapi.public import getDepth, getTicker, getTradeFee, getTradeHistory
from modules.btceapi.trade import TradeAPI
from modules.btceapi.scraping import scrapeMainPage
from modules.btceapi.keyhandler import KeyHandler
from modules.btceapi.common import all_currencies, all_pairs, max_digits, min_orders,\
                   formatCurrency, formatCurrencyDigits, \
                   truncateAmount, truncateAmountDigits, \
                   validatePair, validateOrder, \
                   BTCEConnection
