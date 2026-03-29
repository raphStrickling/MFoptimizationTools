import pytest


@pytest.fixture
def test_root(pytestconfig):
    return pytestconfig.rootpath / "tests"


@pytest.fixture
def test_tmp(test_root):
    return test_root / "tmp"
