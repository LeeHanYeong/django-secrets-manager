class Secrets:
    def get(self, key, default=None):
        raise NotImplementedError('subclasses of Secrets must provice a get() method')
