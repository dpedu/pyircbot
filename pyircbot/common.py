from time import time
from math import floor


class burstbucket(object):
    def __init__(self, maximum, interval):
        """
        Burst bucket class for rate limiting
        :param maximum: maximum value in the bucket
        :param interval: how often a whole item is added to the bucket
        """
        # How many messages can be bursted
        self.bucket_max = maximum
        # how often the bucket has 1 item added
        self.bucket_period = interval
        # last time the burst bucket was filled
        self.bucket_lastfill = time()

        self.bucket = self.bucket_max

    def get(self):
        """
        Return 0 if no sleeping is necessary to rate limit. Otherwise, return the number of seconds to sleep. This
        method should be called again by the user after sleeping
        """
        # First, update the bucket
        # Check if $period time has passed since the bucket was filled
        since_fill = time() - self.bucket_lastfill
        if since_fill > self.bucket_period:
            # How many complete points are credited
            fills = floor(since_fill / self.bucket_period)
            self.bucket += fills
            if self.bucket > self.bucket_max:
                self.bucket = self.bucket_max
            # Advance the lastfill time appropriately
            self.bucket_lastfill += self.bucket_period * fills

        if self.bucket >= 1:
            self.bucket -= 1
            return 0
        return self.bucket_period - since_fill
