from gladier import GladierBaseTool, generate_flow_definition


def untar(**data):
    import tarfile
    import pathlib

    def safe_extract(tar: tarfile.TarFile, path: pathlib.Path):
        """Check all paths in a tarfile before extraction. It's possible that
        paths are non-relative and would otherwise extract to a non-local or
        absolute path.

        :raises ValueError: If a relative path within the tar would extract to
            a location outside of a tar"""
        for member in tar.getmembers():
            member_path = path / member.name
            # Raises ValueError if member_path not relative to path
            member_path.relative_to(path)

        tar.extractall(path)

    untar_input = pathlib.Path(data['untar_input']).expanduser()
    if data.get('untar_output', ''):
        untar_output = pathlib.Path(data['untar_output']).expanduser()
    else:
        untar_output = untar_input.parent / untar_input.stem

    with tarfile.open(untar_input) as file:
        untar_output.mkdir(parents=True, exist_ok=True)
        safe_extract(file, untar_output)

    return str(untar_output)


@generate_flow_definition(modifiers={
    'untar': {'ExceptionOnActionFailure': True,
              'WaitTime': 300}
})
class UnTar(GladierBaseTool):
    """
    The UnTar tool makes it possible to extract data from Tar archives. FuncX Functions:

    * untar (funcx_endpoint_compute)

    :param untar_input: Input directory to archive.
    :param untar_output: (optional) output file to save the new archive. Defaults to the original  # noqa
                       input file with an extension '.tgz' removed.
    :param funcx_endpoint_compute: By default, uses the ``compute`` funcx endpoint.  # noqa
    :returns path: The output location of the extracted archive
    :raises ValueError: If any files within the tar would extract to a non-relative location
    :raises FileNotFoundError: If the file does not exist.
    """

    funcx_functions = [untar]
    required_input = [
            'untar_input',
            'funcx_endpoint_compute',
        ]
