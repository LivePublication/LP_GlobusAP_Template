import pytest
import tarfile
from unittest.mock import Mock


@pytest.fixture
def mock_tar(monkeypatch):
    mock_tf = Mock()
    mock_open = Mock()
    mock_open.return_value.__enter__ = Mock(return_value=mock_tf)
    mock_open.return_value.__exit__ = Mock(return_value=None)
    monkeypatch.setattr(tarfile, 'open', mock_open)

    tarmembers = [tarfile.TarInfo(t) for t in
                  ('one.txt', 'two.txt', 'three.txt')]
    mock_tf.getmembers.return_value = tarmembers
    return mock_open, mock_tf
