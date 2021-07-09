class ConfError(Exception):
    """Exception representing an error in the network configuration's contents."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause

class InstError(Exception):
    """Exception representing an error during network instantation."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause

class DckError(Exception):
    """Exception representing an error related to the docker engine."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause
