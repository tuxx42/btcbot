from time import time


class TokenBucket(object):

    """
    An implementation of the token bucket algorithm.
    """

    def __init__(self, n_req):
        """
        Initialize a request limiting token bucket.

        Input:
            n_req       number of requests per second (integer)
        """
        self.capacity = n_req
        self._n_req = n_req
        self.fill_rate = float(n_req)
        self.timestamp = time()

    def may_i(self):

        """
        Consume tokens from the bucket.
        Returns True if there were sufficient tokens otherwise False.
        """

        if self.n_req > 0:
            self._n_req -= 1
        else:
            return False
        return True

    def get_tokens(self):

        """
        Update and return the current number of available tokens/requests
        """

        if self._n_req < self.capacity:
            now = time()
            # how many tokens have been made available since the last comsume
            delta = self.fill_rate * (now - self.timestamp)
            # update the number of availabe tokens (limited by max capacity)
            self._n_req = min(self.capacity, self._n_req + delta)
            # update timestamp of last consume
            self.timestamp = now
        return self._n_req
    n_req = property(get_tokens)
