from lib.config import generate_random_password
from lib.config import Config, ConfigError
import pytest


def test_passwords():
    for size in xrange(0, 16):
        password = generate_random_password(size=size)
        assert len(password) == size

    password = generate_random_password(size=-1)
    assert len(password) == 0


def test_config():
    config = Config()
    with pytest.raises(ConfigError):
        config.get('common', 'nonexisitingvalue')
    with pytest.raises(ConfigError):
        config.read_from('tests/bad_config.ini')

    config.read_from('tests/good_config.ini')
