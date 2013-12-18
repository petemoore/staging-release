from lib.which import which

def test_exists():
    assert which('python') is not None

def test_does_not_exist():
    assert which('not_existing') is None
