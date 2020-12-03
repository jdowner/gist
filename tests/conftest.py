import gist.client
import pytest


@pytest.fixture(autouse=True)
def disable_stdout_wrapper(monkeypatch):
    monkeypatch.setattr(gist.client, "wrap_stdout_for_unicode", lambda: None)
