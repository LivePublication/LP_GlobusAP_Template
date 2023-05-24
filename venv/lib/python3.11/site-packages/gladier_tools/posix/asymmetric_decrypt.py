from gladier import GladierBaseTool, generate_flow_definition


def asymmetric_decrypt(**data):
    import os
    from cryptography.hazmat.primitives.serialization import \
        load_ssh_private_key
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    private_file = data['private_key_path']
    if '~' in private_file:
        private_file = os.path.expanduser(private_file)

    password = data.get('asym_decrypt_password', None)

    with open(private_file, 'rb') as pri_file:
        private_key = load_ssh_private_key(pri_file.read(), password)

    infile = data['asym_decrypt_file']
    if '~' in infile:
        infile = os.path.expanduser(infile)

    with open(infile, 'rb') as in_file:
        ciphertext = in_file.read()

    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    output_file = data.get('output_file', infile[:len(infile)-4])
    if '~' in output_file:
        output_file = os.path.expanduser(infile)

    with open(output_file, 'wb') as outfile:
        outfile.write(plaintext)

    return output_file


@generate_flow_definition
class AsymmetricDecrypt(GladierBaseTool):
    """
    The Asymmetric Decrypt tool takes in a file encrypted by the asymmetric
    encryption tool and  the path to the RSA public key to perform decryption
    on the file.
    The output file can be passed in as a flow_input. If no output file
    passed, the last 4 characters (.rsa) of the input file are removed.
    It has not been found to be compatible with 3rd party encryption/decryption
    tools.

    FuncX Functions:

    * asymmetric_decrypt (funcx_endpoint_compute)

    :param private_key_path: Path to the id_rsa file which contains
        the RSA private key. Defaults to ~/.ssh/id_rsa if not passed in.
    :param asym_decrypt_file: File which needs to be decrypted.
    :param funcx_endpoint_compute: By default, uses the ``compute``
        funcx endpoint.
    :param asym_decrypt_password: (Optional) If the private file is password
        protected, pass it in through this argument.
    :param output_file: (Optional) Path to the output file which holds the
        decrypted contents.
    :returns output_path: Location of the decrypted file.
    """

    funcx_functions = [asymmetric_decrypt]
    required_input = [
        'private_key_path',
        'asym_decrypt_file',
        'funcx_endpoint_compute'
    ]

    flow_input = {
        'private_key_path': '~/.ssh/id_rsa'
    }
