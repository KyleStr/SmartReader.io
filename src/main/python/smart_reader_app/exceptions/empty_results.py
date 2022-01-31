class EmptyResultsException(Exception):

    def __init__(self, code, status_code=None, payload=None):
        Exception.__init__(self)
        self.code = code
        self.message = "Empty results"
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['code'] = self.code
        return rv
    