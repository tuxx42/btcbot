#!/usr/bin/env python3
from exapi import ExAPI
import modules.krakenex
import base64
import getpass
import io
import time
from depth import depth

from Crypto.Cipher import AES
from Crypto.Hash import MD5

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

        pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * kraken.PADDING
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
            base64.b64decode(e)).decode("utf-8").rstrip(kraken.PADDING)

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
            print (res)
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

    def depth(self, pair='btc_eur', count=20):
        try:
            s = self.k.query_public('Depth', {'pair': kraken.pairs[pair]})
        except Exception as e:
            log.exception(e)
            raise

        if s['error']:
            print ("an error occured %s" % s['error'])
            raise Exception(s['error'])

        d = [depth(**v) for k, v in s['result'].items()][0]
        self.curdepth[pair] = [d, time.time()]
        return d
