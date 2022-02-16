from singupy.hello import singubot


def test_hello_user():
    obj = singubot.UserBot(user_initials="ABC")
    assert obj.say_hey() == "Well hello there ABC!"
