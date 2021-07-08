class IP2Error(Exception):
    """Exception representing an error when running an iproute2 command."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause

class UtilError(Exception):
    """Exception representing an error when calling functions in the utils module."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause
