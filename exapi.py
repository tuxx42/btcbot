class ExAPI():
    def cipher_key(self, dummy=None):
        pass

    def decipher_key(self, dummy=None):
        pass

    def get_balance(self, dummy=None):
        pass

    def add_order(self, order, price, vol):
        pass

    def get_trades(self, **kwargs):
        pass

    def get_min_bid(self):
        return self.current_depth[-1][0].get_min_bid()

    def get_fees(self, **kwargs):
        pass

    def get_max_ask(self):
        return self.current_depth[-1][0].get_max_ask()

    def get_depth(self, **kwargs):
        pass
