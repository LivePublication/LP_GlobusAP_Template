import pathlib
from gladier_tools.posix.tar import tar


def test_tar_home_directory(mock_tar):
    output_file = tar(tar_input='~/foo')
    assert output_file == str(pathlib.Path('~/foo.tgz').expanduser())


def test_tar(mock_tar):
    mock_open, mock_context_manager = mock_tar
    output_file = tar(tar_input='foo')
    assert mock_open.called
    assert mock_context_manager.add.called
    assert output_file == 'foo.tgz'


def test_tar_trailing_slash(mock_tar):
    """This previously could result in /foo/.tgz"""
    output_file = tar(tar_input='/foo/')
    assert output_file == '/foo.tgz'


def test_tar_input_home(mock_tar):
    output_file = tar(tar_input='~/foo')
    assert output_file == str(pathlib.Path('~/foo.tgz').expanduser())


def test_tar_output_home(mock_tar):
    output_file = tar(tar_input='~/foo', tar_output='~/tmp/bar.tgz')
    assert output_file == str(pathlib.Path('~/tmp/bar.tgz').expanduser())
