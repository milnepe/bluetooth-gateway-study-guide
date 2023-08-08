"""Custom exceptions"""


class StateError(RuntimeError):
    """Device state error"""

    def __init__(self, arg):
        self.args = str(arg)


class UnsupportedError(RuntimeError):
    """Device unsupported error"""

    def __init__(self, arg):
        self.args = str(arg)
