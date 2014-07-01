from Crypto.Cipher import AES
from Crypto.Hash import MD5
import base64

import logging
log = logging.getLogger(__name__)


class KeyMgmt(object):
    def __init__(self, ):
        self.key = None
        self.secret = None

    # @Joel: das ist sowas wie ein ueberladener constructor
    @classmethod
    def from_file(cls, filename, password=None, padding='{'):
        with open(filename, 'r') as fd:
            encoded_key = fd.read()

        if password:
            h = MD5.new()
            h.update(password.encode('utf-8'))
            secret = h.hexdigest()
            cipher = AES.new(secret)

        # decode the encoded string
        try:
            decoded = KeyMgmt.decode_AES(cipher, encoded_key, padding)
        except Exception as e:
            log.error('Failed to decode Keyfile: %s', e)
            raise

        if decoded is None:
            raise Exception('Failed to decode Keyfile')

        cls.key, cls.secret = decoded.splitlines()[:2]
        return cls

    @classmethod
    def from_string(cls, secret, key, password=None):
        if password:
            # TODO
            raise Exception(
                'Password not yet supported for keymgmt from string'
            )

        cls.key = key
        cls.secret = secret
        return cls

    @staticmethod
    def decode_AES(encrypted, encoded_key, padding):
        return encrypted.decrypt(
            base64.b64decode(encoded_key)).decode("utf-8").rstrip(padding)
