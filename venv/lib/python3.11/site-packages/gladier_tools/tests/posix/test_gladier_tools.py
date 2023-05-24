import pytest
from gladier import GladierBaseClient, generate_flow_definition

GLADIER_TOOLS = [
    # Posix
    'gladier_tools.posix.Tar',
    'gladier_tools.posix.UnTar',
    'gladier_tools.posix.Encrypt',
    'gladier_tools.posix.Decrypt',
    'gladier_tools.posix.AsymmetricEncrypt',
    'gladier_tools.posix.AsymmetricDecrypt',
    'gladier_tools.posix.HttpsDownloadFile',

    # Globus
    'gladier_tools.globus.Transfer',

    # Publish
    'gladier_tools.publish.Publish',
]


@pytest.mark.parametrize('import_string', GLADIER_TOOLS)
def test_use_gladier_tool(import_string):

    @generate_flow_definition
    class MyGladierClass(GladierBaseClient):
        gladier_tools = [import_string]

    MyGladierClass(auto_login=False)
