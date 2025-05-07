"""Tests the blueprint's HTTP endpoint."""

from pyausec.my_object import MyCoolObject


def test_my_cool_object():
    my_obj = MyCoolObject("Hello, World!")
    assert my_obj.get_message() == "Hello, World!"


def test_my_cool_object_fixture(my_cool_object):
    assert my_cool_object.get_message() == "Hello, World!"
