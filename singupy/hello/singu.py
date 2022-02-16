"""
A test module for singupy, just for fun. Will be deleted later.
"""
import logging

# Initialize log
log = logging.getLogger(__name__)


class SinguBot:
    """
    Class used for testing of library setup only, barely does anything.

    Attributes
    ----------
    name : str
        name of the bot.

    Methods
    ----------
    say_hi()
        Will print hello message to log and also return it as a string.
    """
    def __init__(self, name):
        self.name = name
        log.info(f"The SinguBot {self.name} is now here to stay for as long as you like!")

    def say_hey(self):
        log.info("Returning hello message as a string.")
        return "Well hello there " + self.name + "!"
