import modules.btceapi

#    pair = "btc_usd"


class Btce:
    def __init__(self, passwd=None):
        pass

    def decipher_key(self):
        pass

    def get_balance(self, dummy=None):
        pass

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_depth(self, **kwargs):
        print(repr(kwargs))
        asks, bids = modules.btceapi.getDepth(kwargs)
        print(repr(asks))
        print(repr(bids))
