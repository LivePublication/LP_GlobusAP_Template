from gladier import GladierBaseTool
from typing import Tuple, List, Mapping


def publishv2_gather_metadata(
    dataset: str,
    destination: str,
    source_collection: str,
    destination_collection: str,
    index: str,
    visible_to: List[str],
    entry_id: str = "metadata",
    metadata: Mapping = None,
    source_collection_basepath: str = None,
    destination_url_hostname: str = None,
    checksum_algorithms: Tuple[str] = ("sha256", "sha512"),
    metadata_dc_validation_schema: str = None,
    enable_publish: bool = True,
    enable_transfer: bool = True,
    enable_meta_dc: bool = True,
    enable_meta_files: bool = True,
    **data,
):
    import hashlib
    import urllib
    import pathlib
    import datetime
    import mimetypes
    import traceback

    try:
        import puremagic
    except ImportError:
        puremagic = None

    def translate_guest_collection_path(collection_basepath, path):
        if not collection_basepath:
            return str(path)
        try:
            return f"/{str(pathlib.PosixPath(path).relative_to(collection_basepath))}"
        except ValueError:
            raise ValueError(
                f'POSIX path given "{path}" outside Gloubus Collection '
                f"share path: {collection_basepath}"
            ) from None

    def get_mimetype(filename):
        """
        Attempt to determine the mimetype of a file with a few different approaches, from
        top to bottom in this list:
        1. Try puremagic if it is installed
        2. Use the built in mimetypes lib
        3. Check for text vs binary by reading a chunk of data
        """

        def detect_mimetype(filename):
            if puremagic is not None:
                try:
                    return puremagic.magic_file(str(filename))[0].mime_type
                except (IndexError, ValueError):
                    """Skip puremagic on IndexError (No mimetype could be found) or on ValueError
                    (file was empty)."""
                    pass

            mt, _ = mimetypes.guess_type(filename, strict=True)
            return mt

        def detect_text_or_binary(filename):
            """Read the first 1024 and attempt to decode it in utf-8. If this succeeds,
            the file is determined to be text. If not, its binary.

            There are better ways to do this, but this should be 'good enough' for most
            use-cases we have.
            """
            with open(filename, "rb") as f:
                chunk = f.read(1024)
            try:
                chunk.decode("utf-8")
                return "text/plain"
            except UnicodeDecodeError:
                return "application/octet-stream"

        for func in (detect_mimetype, detect_text_or_binary):
            mimetype = func(filename)
            if mimetype:
                return mimetype

    def get_remote_file_manifest(filepath, destination_path, url_host, algorithms):
        dataset = pathlib.Path(filepath)
        destination = pathlib.Path(destination_path)
        if not dataset.exists():
            raise ValueError(f"File does not exist: {filepath}")

        file_list = [dataset] if dataset.is_file() else list(dataset.iterdir())
        file_list = [
            (
                local_abspath,
                destination
                / str(local_abspath.relative_to(dataset.parent)).lstrip("/"),
            )
            for local_abspath in file_list
        ]

        manifest_entries = []
        for subfile, remote_short_path in file_list:
            rfm = {alg: compute_checksum(subfile, alg) for alg in algorithms}
            # mimetype = analysis.mimetypes.detect_type(subfile)
            rfm.update(
                {
                    "filename": subfile.name,
                    "url": urllib.parse.urlunsplit(
                        (
                            "globus",
                            destination_collection,
                            str(remote_short_path),
                            "",
                            "",
                        )
                    ),
                    "mime_type": get_mimetype(subfile),
                }
            )
            if url_host:
                url_host_p = urllib.parse.urlparse(url_host)
                if not url_host_p.scheme or not url_host_p.netloc:
                    raise ValueError(
                        f"destination_url_hostname {url_host} must be of format: https://example.com"
                    )
                rfm["https_url"] = urllib.parse.urlunsplit(
                    (
                        url_host_p.scheme,
                        url_host_p.hostname,
                        str(remote_short_path),
                        "",
                        "",
                    )
                )

            if subfile.exists():
                rfm["length"] = subfile.stat().st_size
            manifest_entries.append(rfm)
        return manifest_entries

    def compute_checksum(file_path, algorithm, block_size=65536):
        alg = getattr(hashlib, algorithm, None)
        if not alg:
            raise ValueError(f"Algorithm {algorithm} is not available in hashlib!")
        alg_instance = alg()
        with open(file_path, "rb") as open_file:
            buf = open_file.read(block_size)
            while len(buf) > 0:
                alg_instance.update(buf)
                buf = open_file.read(block_size)
        return alg_instance.hexdigest()

    def get_dc(title, subject: str, files: list = None):
        dt = datetime.datetime.now()
        return {
            "identifiers": [
                {
                    "identifierType": "GlobusSearchSubject",
                    "identifier": subject,
                }
            ],
            "creators": [{"name": ""}],
            "dates": [{"date": f"{dt.isoformat()}Z", "dateType": "Created"}],
            "formats": list({f["mime_type"] for f in files}),
            "publicationYear": str(dt.year),
            "publisher": "",
            "types": {"resourceType": "Dataset", "resourceTypeGeneral": "Dataset"},
            "subjects": [],
            "titles": [{"title": dataset.name}],
            "version": "1",
            "schemaVersion": "http://datacite.org/schema/kernel-4",
        }

    def get_content(title, subject, metadata):
        new_metadata = {}
        if enable_meta_files:
            new_metadata["files"] = get_remote_file_manifest(
                dataset, destination, destination_url_hostname, checksum_algorithms
            )
        if enable_meta_dc:
            new_metadata["dc"] = get_dc(title, subject, new_metadata.get("files", []))
            if metadata and "dc" in metadata:
                new_metadata["dc"].update(metadata.pop("dc"))
        new_metadata.update(metadata if metadata is not None else {})
        if metadata_dc_validation_schema:
            import datacite
            import jsonschema

            try:
                # Secondary import required due to these not being exposed as public items, even
                # though the docs recommend using them as such. Explicit imports add them to the
                # module listing so getattr() will work properly to choose the correct one.
                from datacite import schema40, schema41, schema42, schema43

                schema = getattr(datacite, metadata_dc_validation_schema)
                schema.validator.validate(new_metadata["dc"])
            except jsonschema.exceptions.ValidationError:
                raise ValueError(traceback.format_exc()) from None
        return new_metadata

    dataset = pathlib.Path(dataset)
    destination_path = pathlib.Path(destination) / dataset.name
    subject = urllib.parse.urlunparse(
        ("globus", destination_collection, str(destination_path), "", "", "")
    )
    return {
        "search": {
            "id": entry_id,
            "content": get_content(dataset.name, subject, metadata),
            "subject": subject,
            "visible_to": visible_to,
            "search_index": index,
        },
        "transfer": {
            "source_endpoint_id": source_collection,
            "destination_endpoint_id": destination_collection,
            "transfer_items": [
                {
                    "source_path": translate_guest_collection_path(
                        source_collection_basepath, dataset
                    ),
                    "destination_path": str(destination_path),
                }
            ],
        },
    }


class Publishv2(GladierBaseTool):
    """Publish tooling is an extension to the original publish gladier tool, and allows
    for similar style publication of files and folders without the globus-pilot requirement.

    Publishv2 allows for specifying a file or folder on a Globus Collection, and "publishing" the
    data. Publication consists of first gathering metadata on the file or folder, cataloguing the
    metadata with Globus Search, and transferring the file or folder to a Globus Collection. Additional
    metadata may be provided for the ingest step, and several options exist for modifying what
    metadata is automatically gathered.

    Dependencies:

    * None!

    Optional Dependencies:

    * puremagic -- Better mimetype detection
    * datacite -- Validation of Datacite (dc) metadata

    FuncX Functions:

    Publishv2 uses one function called 'publishv2_gather_metadata'. For using custom generated metadata from another
    function, it can be handy to generate the entire 'publishv2_gather_metadata' input block and pass it as flow input
    instead, which can be done via the following:

    .. code-block::

        @generate_flow_definition(modifiers={
            'publishv2_gather_metadata': {'payload': '$.MyCustomPayload.details.results[0].output'},
        })

    This tool nests input under the 'publishv2' keyword. An example is below:

    .. code-block::

        'publishv2': {
            'dataset': 'foo.txt',
            'destination': '/~/my-test-dir',
            'source_collection': 'my-source-globus-collection',
            'destination_collection': 'my-destination-globus-collection',
            'index': 'my-globus-search-index-uuid',
            'visible_to': ['public'],
            # Ingest and Transfer are disabled by default, allowing for 'dry-run' testing.
            # 'ingest_enabled': True,
            # 'transfer_enabled': True,
        },
        'funcx_endpoint_non_compute': '4b116d3c-1703-4f8f-9f6f-39921e5864df',

    :param dataset: Path to file or directory, which will be catalogued in Globus Search and transferred
        to the remote destination
    :param destination: Location on destination collection where data should be stored
    :param source_collection: The source Globus Collection where data is stored
    :param destination_collection: The destination Collection to transfer the ``dataset``
    :param index: The index to ingest this dataset in Globus Search
    :param visible_to: (list[str] Default: ['public']) A list of URN user or group identities for controlling
        access.
    :param entry_id: (str Default:'metadata') The entry id to use in the Globus Search record
    :param metadata: (dict) Extra metadata to include in this search record
    :param source_collection_basepath: Share path if this is a Guest Collection, so that the proper
        source path can be constructed for the transfer document
    :param destination_url_hostname: Adds "https_url" to each file in the 'files' document using this
        provided hostname
    :param checksum_algorithms: (tuple Default:('sha256', 'sha512')) Checksums to use for file metadata
    :param metadata_dc_validation_schema: (str) Schema used to validate datacite (dc) metadata. Possible values
        are (schema40, schema41, schema42, schema43). Recommended schema43. Requires datacite
        package installed on funcx endpoint.
    :param enable_publish: (bool Default: True) Enable the ingest step on the flow. If false, ingest will be
        skipped.
    :param enable_transfer: (bool Default: True) Enable Transfer on the flow. If False, data will not be transferred
        to the remote collection.
    :param enable_meta_dc: (bool Default: True) Generate datacite metadata during the 'gathering' funcx function step.
        datacite metadata is stored under the 'dc' key, and can be valiated using metadata_dc_validation_schema=schema43.
        If additional fields are provided via the ``metadata`` parameter, it will override overlapping fields.
    :param enable_meta_files: (bool Default: True) Generate metadata on all files contained within the dataset. Files
        conforms to BDBag Remote File Manifests, generating a list of entries for each file with keys:
        ('url', 'sha256', 'sha512', 'filename', 'length'). Files may also contain extended keys ('mime_type', 'https_url')
    :param funcx_endpoint_non_compute: A funcX endpoint uuid for gathering metadata.
    """

    flow_definition = {
        "Comment": "Publish metadata to Globus Search, with data from the result.",
        "StartAt": "Publishv2GatherMetadata",
        "States": {
            "Publishv2GatherMetadata": {
                "Comment": "Generate search metadata and a transfer document",
                "Type": "Action",
                "ActionUrl": "https://compute2.dev.funcx.org/fxap",
                "ExceptionOnActionFailure": True,
                "Parameters": {
                    "tasks": [
                        {
                            "endpoint.$": "$.input.funcx_endpoint_non_compute",
                            "function.$": "$.input.publishv2_gather_metadata_funcx_id",
                            "payload.$": "$.input.publishv2",
                        }
                    ]
                },
                "ResultPath": "$.Publishv2GatherMetadata",
                "WaitTime": 600,
                "Next": "Publishv2ChoiceTransfer",
            },
            "Publishv2ChoiceTransfer": {
                "Comment": "Determine if the document should be cataloged in Globus Search",
                "Type": "Choice",
                "Choices": [
                    {
                        "And": [
                            {
                                "Variable": "$.input.publishv2.transfer_enabled",
                                "IsPresent": True,
                            },
                            {
                                "Variable": "$.input.publishv2.transfer_enabled",
                                "BooleanEquals": True,
                            },
                        ],
                        "Next": "Publishv2Transfer",
                    }
                ],
                "Default": "Publishv2SkipTransfer",
            },
            "Publishv2Transfer": {
                "Comment": "Transfer files for publication",
                "Type": "Action",
                "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
                "InputPath": "$.Publishv2GatherMetadata.details.results[0].output.transfer",
                "ResultPath": "$.Publishv2Transfer",
                "WaitTime": 600,
                "Next": "Publishv2ChoiceIngest",
            },
            "Publishv2SkipTransfer": {
                "Comment": "The ingest step has been skipped",
                "Type": "Pass",
                "Next": "Publishv2ChoiceIngest",
            },
            "Publishv2ChoiceIngest": {
                "Comment": "Determine if the document should be cataloged in Globus Search",
                "Type": "Choice",
                "Choices": [
                    {
                        "And": [
                            {
                                "Variable": "$.input.publishv2.ingest_enabled",
                                "IsPresent": True,
                            },
                            {
                                "Variable": "$.input.publishv2.ingest_enabled",
                                "BooleanEquals": True,
                            },
                        ],
                        "Next": "Publishv2Ingest",
                    }
                ],
                "Default": "Publishv2SkipIngest",
            },
            "Publishv2Ingest": {
                "Comment": "Ingest the search document",
                "Type": "Action",
                "ActionUrl": "https://actions.globus.org/search/ingest",
                "InputPath": "$.Publishv2GatherMetadata.details.results[0].output.search",
                "ResultPath": "$.Publishv2Ingest",
                "WaitTime": 300,
                "Next": "Publishv2Done",
            },
            "Publishv2SkipIngest": {
                "Comment": "The ingest step has been skipped",
                "Type": "Pass",
                "Next": "Publishv2Done",
            },
            "Publishv2Done": {
                "Comment": "The Publication tool has completed successfully.",
                "Type": "Pass",
                "End": True,
            },
        },
    }

    required_input = [
        "publishv2",
        "funcx_endpoint_non_compute",
    ]

    flow_input = {}

    funcx_functions = [
        publishv2_gather_metadata,
    ]
