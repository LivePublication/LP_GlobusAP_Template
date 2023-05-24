import pytest
import pathlib
import json
from datacite import schema42, schema43
from gladier_tools.publish.publishv2 import publishv2_gather_metadata

mock_data = pathlib.Path(__file__).resolve().parent.parent / "mock_data/publish/"

minimum_dc_metadata = {
    "creators": [{"name": ""}],
    "identifiers": [
        {
            "identifier": "globus://my_globus_collection/my-new-project/test_dataset_folder",
            "identifierType": "GlobusSearchSubject",
        }
    ],
    "dates": [{"date": "2023-03-16T07:44:14.044091", "dateType": "Created"}],
    "formats": ["text/plain"],
    "publicationYear": "2023",
    "publisher": "",
    "types": {"resourceType": "Dataset", "resourceTypeGeneral": "Dataset"},
    "subjects": [],
    "titles": [{"title": "test_dataset_folder"}],
    "version": "1",
    "schemaVersion": "http://datacite.org/schema/kernel-4",
}


@pytest.fixture
def publish_input():
    return {
        "dataset": mock_data / "test_dataset_folder",
        "destination": "/my-new-project",
        "source_collection": "my_transfer_endpoint",
        "destination_collection": "my_globus_collection",
        "destination_collection_basepath": "/my-new-project/",
        "index": "my_index",
        "visible_to": ["public"],
        "enable_metadata_dc": True,
        "groups": [],
    }


def test_publish(publish_input):
    publishv2_gather_metadata(**publish_input).keys() == ("search", "transfer")


def test_json_serializable(publish_input):
    assert json.dumps(publishv2_gather_metadata(**publish_input))


def test_publish_dc(publish_input):
    output = publishv2_gather_metadata(**publish_input)
    content = output["search"]["content"]
    assert "dc" in content
    partial_dc = content["dc"].copy()
    partial_dc.pop("dates")
    assert partial_dc == {
        "creators": [{"name": ""}],
        "identifiers": [
            {
                "identifier": "globus://my_globus_collection/my-new-project/test_dataset_folder",
                "identifierType": "GlobusSearchSubject",
            }
        ],
        # timestamp contains seconds, which is hard to check. Skip it!
        # '2023-03-17T17:14:31.832955Z'
        # 'dates': [{'date': '2023-03-16T07:44:14.044091', 'dateType': 'Created'}],
        "formats": ["text/plain"],
        "publicationYear": "2023",
        "publisher": "",
        "types": {"resourceType": "Dataset", "resourceTypeGeneral": "Dataset"},
        "subjects": [],
        "titles": [{"title": "test_dataset_folder"}],
        "version": "1",
        "schemaVersion": "http://datacite.org/schema/kernel-4",
    }
    assert "dates" in content["dc"]
    assert content["dc"]["dates"][0]["dateType"] == "Created"
    assert "date" in content["dc"]["dates"][0]


def test_validate_dc(publish_input):
    dc = publishv2_gather_metadata(**publish_input)["search"]["content"]["dc"]
    schema42.validator.validate(dc)
    schema43.validator.validate(dc)


@pytest.mark.parametrize(
    "schema,metadata",
    [
        (
            "schema40",
            {
                "identifier": {
                    "identifier": "https://doi.org/10.14454/3w3z-sa82",
                    "identifierType": "DOI",
                },
                "creators": [{"creatorName": "foo"}],
                "publicationYear": "2023",
                "publisher": "FOO",
                "resourceType": {
                    "resourceType": "Dataset",
                    "resourceTypeGeneral": "Dataset",
                },
                "titles": [{"title": "test_dataset_folder"}],
            },
        ),
        (
            "schema41",
            {
                "identifier": {
                    "identifier": "https://doi.org/10.14454/3w3z-sa82",
                    "identifierType": "DOI",
                },
                "creators": [{"creatorName": "foo"}],
                "publicationYear": "2023",
                "publisher": "FOO",
                "resourceType": {
                    "resourceType": "Dataset",
                    "resourceTypeGeneral": "Dataset",
                },
                "titles": [{"title": "test_dataset_folder"}],
            },
        ),
        ("schema42", minimum_dc_metadata),
        ("schema43", minimum_dc_metadata),
    ],
)
def test_eval(schema, metadata, publish_input):
    publish_input["metadata"] = {"dc": metadata}
    publish_input["enable_meta_dc"] = False
    publish_input["metadata_dc_validation_schema"] = schema
    publishv2_gather_metadata(**publish_input)


def test_datacite_override(publish_input):
    extra_input = {
        "metadata": {"dc": {"creators": [{"name": "nick"}]}},
        "metadata_dc_validation_schema": "schema43",
    }
    publish_input.update(extra_input)
    output = publishv2_gather_metadata(**publish_input)["search"]["content"]["dc"]
    assert output["creators"] == [{"name": "nick"}]


def test_datacite_validator(publish_input):
    extra_input = {
        "metadata": {"dc": {"authors": ["invalid_bob"]}},
        "metadata_dc_validation_schema": "schema43",
    }
    publish_input.update(extra_input)
    with pytest.raises(ValueError):
        publishv2_gather_metadata(**publish_input)


def test_publish_files(publish_input):
    output = publishv2_gather_metadata(**publish_input)
    files = output["search"]["content"]["files"]
    files.sort(key=lambda x: x["filename"])
    assert files == [
        {
            "sha256": "49606feb430b0ca35c4099c1e84fe81b5634039ecbeb408d76fa5e44f93c1d9a",
            "sha512": "3a9db7ddff3f83902624832a74ba5559e83ef66cb471d14d79a2b89fa981f47b9a0f27ef83f4f266ee5ecf22f817fe58da6f4323c0eb5557fea9152fb4465e04",
            "filename": "bar.txt",
            "url": "globus://my_globus_collection/my-new-project/test_dataset_folder/bar.txt",
            "mime_type": "text/plain",
            "length": 16,
        },
        {
            "sha256": "ef04ad1ddb694bcf461bef6668d387117c63d1648589d55413d4266dc0372dbd",
            "sha512": "aa650e6a730cc73c6d967d9a5c3549dd1bdc94a0128c1ea1fcb9506b5e9c099583e979892af75e2930fb33a84c0c7eb2be5e3e508809f4269cba01ff22847a03",
            "filename": "foo.txt",
            "url": "globus://my_globus_collection/my-new-project/test_dataset_folder/foo.txt",
            "mime_type": "text/plain",
            "length": 16,
        },
    ]


def test_publish_mimetype_csv(publish_input):
    publish_input["dataset"] = mock_data / "1951.csv"
    files = publishv2_gather_metadata(**publish_input)["search"]["content"]["files"]
    assert len(files) == 1
    assert files[0]["mime_type"] == "text/csv"


def test_publish_mimetype_tsv(publish_input):
    publish_input["dataset"] = mock_data / "1951.tsv"
    files = publishv2_gather_metadata(**publish_input)["search"]["content"]["files"]
    assert len(files) == 1
    assert files[0]["mime_type"] == "text/tab-separated-values"


def test_publish_mimetype_bin(publish_input):
    publish_input["dataset"] = mock_data / "random.dat"
    files = publishv2_gather_metadata(**publish_input)["search"]["content"]["files"]
    assert len(files) == 1
    assert files[0]["mime_type"] == "application/octet-stream"


def test_publish_mimetype_bin(publish_input):
    publish_input["dataset"] = mock_data / "test_file.txt"
    files = publishv2_gather_metadata(**publish_input)["search"]["content"]["files"]
    assert len(files) == 1
    assert files[0]["mime_type"] == "text/plain"


def test_https_url(publish_input):
    publish_input["dataset"] = mock_data / "test_file.txt"
    publish_input["destination_url_hostname"] = "https://example.com"
    files = publishv2_gather_metadata(**publish_input)["search"]["content"]["files"]
    assert len(files) == 1
    assert files[0]["https_url"] == "https://example.com/my-new-project/test_file.txt"


def test_https_invalid_dest_hostname(publish_input):
    publish_input["dataset"] = mock_data / "test_file.txt"
    publish_input["destination_url_hostname"] = "example.com"
    with pytest.raises(ValueError):
        publishv2_gather_metadata(**publish_input)


def test_invalid_checksums(publish_input):
    publish_input["checksum_algorithms"] = ["md3"]
    with pytest.raises(ValueError):
        publishv2_gather_metadata(**publish_input)


def test_publish_transfer(publish_input):
    output = publishv2_gather_metadata(**publish_input)
    dataset = publish_input["dataset"]
    assert output["transfer"] == {
        "destination_endpoint_id": "my_globus_collection",
        "source_endpoint_id": "my_transfer_endpoint",
        "transfer_items": [
            {
                "destination_path": str(pathlib.Path("/my-new-project") / dataset.name),
                "source_path": str(dataset),
            }
        ],
    }


def test_publish_collection_valid_basepath(publish_input):
    """Test Guest Collection basepath where the share point is the parent of the source
    dataset being published."""
    publish_input["source_collection_basepath"] = publish_input["dataset"].parent
    source_file = publishv2_gather_metadata(**publish_input)["transfer"]["transfer_items"][0]
    assert source_file["source_path"] == f"/{publish_input['dataset'].name}"


def test_publish_collection_source_basepath_mismatch(publish_input):
    """Test Guest Collection basepath where the share point is the parent of the source
    dataset being published."""
    publish_input["source_collection_basepath"] = (
        publish_input["dataset"].parent / "foo"
    )
    with pytest.raises(ValueError):
        publishv2_gather_metadata(**publish_input)


def test_non_existent_dataset(publish_input):
    publish_input["dataset"] = "/does/not/exist"
    with pytest.raises(ValueError):
        publishv2_gather_metadata(**publish_input)
