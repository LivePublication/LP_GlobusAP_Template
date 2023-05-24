from gladier import GladierBaseTool, generate_flow_definition


def publish_gather_metadata(**data):
    import pathlib
    import traceback
    from pilot.client import PilotClient
    from pilot.exc import PilotClientException, FileOrFolderDoesNotExist

    def translate_guest_collection_path(collection_basepath, path):
        try:
            return f'/{str(pathlib.PosixPath(path).relative_to(collection_basepath))}'
        except ValueError:
            raise ValueError(f'POSIX path given "{path}" outside Gloubus Collection '
                            f'share path: {collection_basepath}') from None

    try:
        dataset, destination = data['dataset'], data.get('destination', '/')
        index, project, groups = data['index'], data['project'], data.get('groups', [])
        source_collection_basepath = data.get('source_collection_basepath', '/')

        # Bootstrap Pilot
        pc = PilotClient(config_file=None, index_uuid=index)
        pc.project.set_project(project)
        # short_path is how pilot internally refers to datasets, implicitly accounting for
        # the endpoint and base project path. After publication, you may refer to your
        # dataset via the short path -- ``pilot describe short_path``
        short_path = pc.build_short_path(dataset, destination)
        return {
            'search': {
                'id': data.get('id', 'metadata'),
                'content': pc.gather_metadata(dataset, destination,
                                              custom_metadata=data.get('metadata')),
                'subject': pc.get_subject_url(short_path),
                'visible_to': ['public' if g == 'public' else f'urn:globus:groups:id:{g}' for g in groups + [pc.get_group()]],
                'search_index': index
            },
            'transfer': {
                'source_endpoint_id': data['source_globus_endpoint'],
                'destination_endpoint_id': pc.get_endpoint(),
                'transfer_items': [{
                    'source_path': translate_guest_collection_path(source_collection_basepath, src),
                    'destination_path': dest,
                    # 'recursive': False,  # each file is explicit in pilot, no directories
                } for src, dest in pc.get_globus_transfer_paths(dataset, destination)]
            }
        }
    except (PilotClientException, FileOrFolderDoesNotExist):
        # FuncX does not allow for custom exceptions. Catch and print any pilot errors
        # so that FuncX does not encounter them.
        return traceback.format_exc()


class Publish(GladierBaseTool):
    """This function uses the globus-pilot tool to generate metadata compatible with
    portals on https://acdc.alcf.anl.gov/. Requires globus_pilot>=0.6.0.

    FuncX Functions:

    * publish_gather_metadata (funcx_endpoint_non_compute)

    Publication happens in three steps:

    * PublishGatherMetadata -- A funcx function which uses globus-pilot to gather
      metadata on files or folders
    * PublishTransfer -- Transfers data to the Globus Endpoint selected in Globus Pilot
    * PublishIngest -- Ingest metadata gathered in fist step to Globus Search

    **Note**: This tool needs internet access to fetch Pilot configuration records, which
    contain the destination endpoint and other project info. The default FuncX endpoint
    name is `funcx_endpoint_non_compute`. You can change this with the following modifier:

    .. code-block::

        @generate_flow_definition(modifiers={
            'publish_gather_metadata': {'endpoint': 'funcx_endpoint_non_compute'},
        })

    More details on modifiers can be found at
    https://gladier.readthedocs.io/en/latest/gladier/flow_generation.html

    NOTE: This tool nests input under the 'pilot' keyword. Submit your input as the following:

    .. code-block::

        {
            'input': {
                'pilot': {
                    'dataset': 'foo',
                    'index': 'my-search-index-uuid',
                    'project': 'my-pilot-project',
                    'source_globus_endpoint': 'ddb59aef-6d04-11e5-ba46-22000b92c6ec',
                }
        }

    :param dataset: Path to file or directory. Used by Pilot to gather metadata, and set as the
        source for transfer to the publication endpoint configured in Pilot.
    :param destination: relative location under project directory to place dataset (Default `/`)
    :param source_globus_endpoint: The Globus Endpoint of the machine where you are executing
    :param source_collection_basepath: If using a guest collection, the posix path of the guest collection.
        Used to translate source paths for the transfer step. (Default: `/`)
    :param index: The index to ingest this dataset in Globus Search
    :param project: The Pilot project to use for this dataset
    :param groups: A list of additional groups to make these records visible_to.
    :param funcx_endpoint_non_compute: A funcX endpoint uuid for gathering metadata. Requires
        internet access.


    Requires: the 'globus-pilot' package to be installed.
    """

    flow_definition = {
        'Comment': 'Publish metadata to Globus Search, with data from the result.',
        'StartAt': 'PublishGatherMetadata',
        'States': {
            'PublishGatherMetadata': {
                'Comment': 'Say something to start the conversation',
                'Type': 'Action',
                'ActionUrl': 'https://compute2.dev.funcx.org/fxap',
                'ExceptionOnActionFailure': False,
                'Parameters': {
                    'tasks': [{
                        'endpoint.$': '$.input.funcx_endpoint_non_compute',
                        'function.$': '$.input.publish_gather_metadata_funcx_id',
                        'payload.$': '$.input.pilot',
                    }]
                },
                'ResultPath': '$.PublishGatherMetadata',
                'WaitTime': 60,
                'Next': 'PublishTransfer',
            },
            'PublishTransfer': {
                'Comment': 'Transfer files for publication',
                'Type': 'Action',
                'ActionUrl': 'https://actions.automate.globus.org/transfer/transfer',
                'InputPath': '$.PublishGatherMetadata.details.results[0].output.transfer',
                'ResultPath': '$.PublishTransfer',
                'WaitTime': 600,
                'Next': 'PublishIngest',
            },
            'PublishIngest': {
                'Comment': 'Ingest the search document',
                'Type': 'Action',
                'ActionUrl': 'https://actions.globus.org/search/ingest',
                'ExceptionOnActionFailure': False,
                'InputPath': '$.PublishGatherMetadata.details.results[0].output.search',
                'ResultPath': '$.PublishIngest',
                'WaitTime': 300,
                'End': True
            },
        }
    }

    required_input = [
        'pilot',
        'funcx_endpoint_non_compute',
    ]

    flow_input = {

    }

    funcx_functions = [
        publish_gather_metadata,
    ]
