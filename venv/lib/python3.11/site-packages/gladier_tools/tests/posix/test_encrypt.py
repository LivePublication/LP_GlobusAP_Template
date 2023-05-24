import pathlib
from gladier_tools.posix.encrypt import encrypt
from unittest.mock import patch, mock_open

MOCK_DATA = bytes('This is a secret file, it shall be encrypted!', 'utf-8')


def test_encrypt():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)) as mock_file:
        encrypt(**{'encrypt_input': 'foo', 'encrypt_key': 'my_secret'})
    mock_file.assert_called_with(pathlib.Path('foo.aes'), 'wb+')


def test_encrypt_custom_outfile():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)) as mock_file:
        encrypt(**{'encrypt_input': 'foo', 'encrypt_key': 'my_secret',
                   'encrypt_output': 'bar.aes'})
    mock_file.assert_called_with(pathlib.Path('bar.aes'), 'wb+')


def test_encrypt_home():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)):
        result = encrypt(**{'encrypt_input': '~/foo', 'encrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/foo.aes').expanduser())


def test_encrypt_buried_path():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)):
        result = encrypt(**{'encrypt_input': '~/bar/baz/foo', 'encrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/bar/baz/foo.aes').expanduser())


def test_encrypt_custom_output():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)):
        result = encrypt(**{'encrypt_input': 'foo.aes', 'encrypt_output': 'bar',
                            'encrypt_key': 'my_secret'})
    assert result == 'bar'


def test_encrypt_custom_output_home():
    with patch('builtins.open', mock_open(read_data=MOCK_DATA)):
        result = encrypt(**{'encrypt_input': '~/foo', 'encrypt_output': '~/bar.enc',
                            'encrypt_key': 'my_secret'})
    assert result == str(pathlib.Path('~/bar.enc').expanduser())
