from singupy.hello import singu


def test_hello_user():
    obj = singu.SinguBot(name="Awesome")
    assert obj.say_hey() == "Well hello there Awesome!"
