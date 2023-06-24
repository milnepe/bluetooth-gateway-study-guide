#!/usr/bin/python

class StateError(RuntimeError):
    def __init__(self, arg):
        self.args = str(arg)


class UnsupportedError(RuntimeError):
    def __init__(self, arg):
        self.args = str(arg)
