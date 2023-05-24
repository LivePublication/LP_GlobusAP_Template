from gladier import GladierBaseTool, generate_flow_definition


def encrypt(**data):
    import pathlib
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash

    password = bytes(data['encrypt_key'], 'utf-8')
    ckdf = ConcatKDFHash(algorithm=hashes.SHA256(), length=32,
                         otherinfo=None)
    key = base64.urlsafe_b64encode(ckdf.derive(password))
    fernet = Fernet(key)

    infile = pathlib.Path(data['encrypt_input']).expanduser()
    if data.get('encrypt_output'):
        outfile = pathlib.Path(data['encrypt_output']).expanduser()
    else:
        outfile = infile.with_suffix(f'{infile.suffix}.aes')

    # Encrypt and write the new file
    with open(infile, 'rb') as file:
        encrypted = fernet.encrypt(file.read())
    with open(outfile, 'wb+') as encrypted_file:
        encrypted_file.write(encrypted)
    return str(outfile)


@generate_flow_definition(modifiers={
    'encrypt': {'ExceptionOnActionFailure': True}
})
class Encrypt(GladierBaseTool):
    """
    The Encrypt tool takes in a file and a password to perform
    128-bit AES symmetric key encryption on the file.
    The original contents of the file are overwritten with the encrypted text.
    Adds an extension (.aes) to the name of the file.
    It has not been found to be compatible with 3rd party encryption/decryption
    tools.

    FuncX Functions:

    * encrypt (funcx_endpoint_compute)

    :param encrypt_input: Path to the file which needs to be encrypted.
    :param encrypt_output: Custom path to outputfile. Default is the same
        file with the '.aes' suffix added
    :param encrypt_key: Symmetric key or "password" which can be used to
        decrypt the encrypted file.
    :param funcx_endpoint_compute: By default, uses the ``compute``
        funcx endpoint.
    :returns output_path: Location of the encrypted file.
    """

    funcx_functions = [encrypt]
    required_input = [
        'encrypt_input',
        'encrypt_key',
        'funcx_endpoint_compute'
    ]
