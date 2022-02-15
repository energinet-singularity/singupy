from singupy.kafkahelper import hellosingu


def test_hello_user():
    obj = hellosingu.HelloSingu(user_initials="ABC")
    assert obj.say_hey() == "Well hello there ABC!"
