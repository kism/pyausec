import logging

from pyausec import __main__


def test_main(caplog):
    caplog.set_level(logging.INFO)
    __main__.main()
    assert "Hello, World!" in caplog.text
    assert "pyausec version: 0.0.1" in caplog.text
    assert "Hello, World!" in caplog.text
