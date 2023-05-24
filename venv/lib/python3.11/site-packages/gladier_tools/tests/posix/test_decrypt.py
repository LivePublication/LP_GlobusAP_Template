import pytest
import pathlib
from gladier_tools.posix.decrypt import decrypt
from unittest.mock import patch, mock_open

MOCK_ENCRYPTED_DATA = bytes('''
gAAAAABhlaEF-8qPrlFItnnr6yhGq3FDvjhXeUtySlPL3YZcthI5AKzMvPxfGkL9k3-O5ASmDo3HfUezlnI4ztq1N4YIZJZG5ew
-HKZAkrKAt24eovme8hGq7ZNBzQh-mc5q-XRfuwGFun2iMS8KKrKrEtoDOYUAC898ekdjqTakMF9zb_-aHjPYpwwNweF-KoxBDi
oVNneg0X0HC3FG-WBEGJsYPLwmYaRiT9xf5Ul7HiLei5wvJe3GxtB5YagmHXsnBnVy5VvM
''', 'utf-8')


def test_decrypt():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)) as mock_file:
        decrypt(**{'decrypt_input': 'foo.aes', 'decrypt_key': 'my_secret'})
    mock_file.assert_called_with(pathlib.Path('foo'), 'wb')


def test_decrypt_bad_secret():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)):
        with pytest.raises(ValueError):
            decrypt(**{'decrypt_input': 'foo.aes', 'decrypt_key': 'bad_secret'})


def test_decrypt_home():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)):
        result = decrypt(**{'decrypt_input': '~/foo.aes', 'decrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/foo').expanduser())


def test_decrypt_buried_path():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)):
        result = decrypt(**{'decrypt_input': '~/bar/baz/foo.aes', 'decrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/bar/baz/foo').expanduser())


def test_decrypt_custom_output():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)):
        result = decrypt(**{'decrypt_input': 'foo.aes', 'decrypt_key': 'my_secret'})
    assert result == 'foo'


def test_decrypt_custom_output_home():
    with patch('builtins.open', mock_open(read_data=MOCK_ENCRYPTED_DATA)):
        result = decrypt(**{'decrypt_input': '~/foo.aes', 'decrypt_output': '~/bar',
                         'decrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/bar').expanduser())
