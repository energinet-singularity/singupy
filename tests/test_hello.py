from singupy import hello


def test_hello_user():
    obj = hello.SinguBot(name="Awesome")
    assert obj.say_hi() == "Well hello there, i am Awesome!"
