from gladier import GladierBaseTool


class Transfer(GladierBaseTool):
    """
    Transfer is a simple single-state flow with no FuncX Functions, which talks directly
    to the Transfer Action Provider. It transfers only a single file or directory.

    :param transfer_source_endpoint_id: Globus Source Endpoint UUID
    :param transfer_destination_endpoint_id: Globus Destination Endpoint UUID
    :param transfer_source_path: Globus Source Path
    :param transfer_destination_path: Globus Destination Path
    :param transfer_recursive: True if this is a directory, false otherwise.
    """

    """
    The Transfer tool makes it possible to transfer data (files/folders) between globus endpoints.

    :param transfer_source_path: Path to the data that needs to be transferred in the source endpoint.
    :param transfer_destination_path: Path where the data will be transferred to in the destination endpoint.
    :param transfer_source_endpoint_id: Globus ID of the endpoint from which data will be transferred.
    :param transfer_destination_endpoint_id: Globus ID of the endpoint to which data will be transferred.
    :param transfer_recursive: Set to True if all the contents within a directory need to be transferred recursively, False otherwise.
    :returns success: Whether or not the transfer was successful.
    """

    flow_definition = {
        'Comment': 'Transfer a file or directory in Globus',
        'StartAt': 'Transfer',
        'States': {
            'Transfer': {
                'Comment': 'Transfer a file or directory in Globus',
                'Type': 'Action',
                'ActionUrl': 'https://actions.automate.globus.org/transfer/transfer',
                'Parameters': {
                    'source_endpoint_id.$': '$.input.transfer_source_endpoint_id',
                    'destination_endpoint_id.$': '$.input.transfer_destination_endpoint_id',
                    'transfer_items': [
                        {
                            'source_path.$': '$.input.transfer_source_path',
                            'destination_path.$': '$.input.transfer_destination_path',
                            'recursive.$': '$.input.transfer_recursive',
                        }
                    ]
                },
                'ResultPath': '$.Transfer',
                'WaitTime': 600,
                'End': True
            },
        }
    }

    flow_input = {
        'transfer_sync_level': 'checksum'
    }
    required_input = [
        'transfer_source_path',
        'transfer_destination_path',
        'transfer_source_endpoint_id',
        'transfer_destination_endpoint_id',
        'transfer_recursive',
    ]
