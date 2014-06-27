#!/usr/bin/env python3
from exapi import ExAPI
import modules.krakenex
import base64
import getpass
import io

from Crypto.Cipher import AES
from Crypto.Hash import MD5


class kraken(ExAPI):
    PADDING = '{'

    def __init__(self, passwd=None):
        try:
            if passwd is None:
                passwd = getpass.getpass("enter key: ")
        except:
            print ("unable to get password")
            raise Exception
        h = MD5.new()
        h.update(passwd.encode('utf-8'))
        secret = h.hexdigest()

        self.cipher = AES.new(secret)

    def cipher_key(self, dummy=None):
        BLOCK_SIZE = 32

        pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * self.PADDING
        EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))

        f = open(self.key, "r")
        decoded = f.readline()
        decoded += f.readline()
        f.close()

        try:
            encoded = EncodeAES(self.cipher, decoded)
        except:
            return None

        print(encoded.decode('utf-8'))
        return encoded

    def decipher_key(self, key):
        # the block size for the cipher object; must be 16, 24, or 32 for AES
        # used to ensure that your value is always a multiple of BLOCK_SIZE

        # one-liner to sufficiently pad the text to be encrypted
        DecodeAES = lambda c, e: c.decrypt(
            base64.b64decode(e)).decode("utf-8").rstrip(self.PADDING)

        f = open(key, "rb")
        encoded = f.readline().strip()
        f.close()

        # decode the encoded string
        try:
            decoded = DecodeAES(self.cipher, encoded)
        except:
            return None

        if decoded is None:
            raise Exception

        self.k = modules.krakenex.API()

        s = io.StringIO(decoded)
        self.k.key = s.readline().strip()
        self.k.secret = s.readline().strip()
        s.close()

    def get_balance(self, dummy=None):
        s = self.k.query_private('Balance')
        if s['error']:
            print ("an error occured while getting the account balance: %s" %
                   s['error'])
            raise Exception
        else:
            balance = {}
            for cur in s['result']:
                if s['result'][cur]:
                    balance[cur] = float(s['result'][cur])
            print (balance)
            return balance

    def add_order(self, order, price, vol, ordertype='limit'):
        s = self.k.query_private('AddOrder',
                                 {'pair': 'XXBTZEUR',
                                  'type': order,
                                  'ordertype': ordertype,
                                  'price': price,
                                  'volume': vol,
                                  })
        print(s)
#        return s

    def get_trades(self, **kwargs):
        try:
            s = self.k.query_public('Trades', kwargs)
        except:
            print ("unable to get trades")
            raise Exception
        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception
        print(s['result'])

    def get_depth(self, **kwargs):
        try:
            s = self.k.query_public('Depth', kwargs)
        except:
            print ("unable to get trades")
            raise Exception
        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception
        return s['result']
