from gladier import GladierBaseTool, generate_flow_definition


def tar(**data):
    import os
    import tarfile
    import pathlib

    tar_input = pathlib.Path(data['tar_input']).expanduser()
    tar_output = data.get('tar_output', f'{tar_input}.tgz')
    tar_output = pathlib.Path(tar_output).expanduser()
    # Move to the parent directory before archiving. This ensures the
    # archive does not contain unnecessary path hierarchy.
    os.chdir(tar_input.parent)
    with tarfile.open(tar_output, 'w:gz') as tf:
        tf.add(tar_input.name)

    return str(tar_output)


@generate_flow_definition(modifiers={
    'tar': {'ExceptionOnActionFailure': True,
            'WaitTime': 300}
})
class Tar(GladierBaseTool):
    """
    The Tar tool makes it possible to create Tar archives from folders. FuncX Functions:

    * tar (funcx_endpoint_compute)

    :param tar_input: Input directory to archive.
    :param tar_output: (optional) output file to save the new archive. Defaults to the original
                       input file with an extension (myfile.tgz) if not given.
    :param funcx_endpoint_compute: By default, uses the ``compute`` funcx endpoint.
    :returns path: The name of the newly created archive.
    """

    funcx_functions = [tar]
    required_input = [
        'tar_input',
        'funcx_endpoint_compute',
    ]
