from gladier import GladierBaseTool, generate_flow_definition


def asymmetric_encrypt(**data):
    import os
    from cryptography.hazmat.primitives.serialization import \
        load_ssh_public_key
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    public_file = data['public_key_path']
    if '~' in public_file:
        public_file = os.path.expanduser(public_file)

    with open(public_file, 'rb') as pub_file:
        public_key = load_ssh_public_key(pub_file.read())

    infile = data['asym_encrypt_file']
    if '~' in infile:
        infile = os.path.expanduser(infile)

    with open(infile, 'rb') as in_file:
        message = in_file.read()

    ciphertext = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    with open(f'{infile}.rsa', 'wb') as outfile:
        outfile.write(ciphertext)

    return f'{infile}.rsa'


@generate_flow_definition
class AsymmetricEncrypt(GladierBaseTool):
    """
    The Asymmetric Encrypt tool takes in a file and the path to the RSA public
    key to perform RSA encryption on the file.
    Adds an extension (.rsa) to the name of the file.
    It has not been found to be compatible with 3rd party encryption/decryption
    tools.

    FuncX Functions:

    * asymmetric_encrypt (funcx_endpoint_compute)

    :param public_key_path: Path to the .pub file which contains
        the RSA public key. Defaults to ~/.ssh/id_rsa.pub
    :param asym_encrypt_file: File which needs to be encrypted.
    :param funcx_endpoint_compute: By default, uses the ``compute``
        funcx endpoint.
    :returns output_path: Location of the encrypted file.
    """

    funcx_functions = [asymmetric_encrypt]
    required_input = [
        'public_key_path',
        'asym_encrypt_file',
        'funcx_endpoint_compute'
    ]
    flow_input = {
        'public_key_path': '~/.ssh/id_rsa.pub'
    }