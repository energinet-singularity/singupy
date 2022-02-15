"""
A test of the singulib, just for fun. Will be deleted later.
"""

import logging

# Initialize log
log = logging.getLogger(__name__)


class HelloSingu:
    def __init__(self, user_initials):
        self.user_initials = user_initials

    def say_hey(self):
        log.info("returned hello message saying hello.")
        return "Well hello there " + self.user_initials + "!"
