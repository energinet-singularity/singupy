import pytest
import os
from kafkahelper import hellosingu 

# Check all files files can be parsed
def test_hello_user():
    obj = hellosingu.HelloSingu(user_initials="ABC")
    pass
    assert obj.say_hey() == "Well hello there ABC!"
