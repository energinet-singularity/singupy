"""
A test module for singupy, just for fun. Will be deleted later.
"""

import logging

# Initialize log
log = logging.getLogger(__name__)


class UserBot:
    def __init__(self, user_initials):
        self.user_initials = user_initials
        log.info(f"SinguBot with initials {self.user_initials} is now here to stay for as long as you like!")

    def say_hey(self):
        log.info("Returning hello message as a string.")
        return "Well hello there " + self.user_initials + "!"
