import pytest
import uuid
import pilot.client
from pilot.exc import PilotClientException
from unittest.mock import Mock
from gladier_tools.publish.publish import publish_gather_metadata


@pytest.fixture
def pilot_input():
    return {
        'dataset': 'my_dataset',
        'index': 'my_index',
        'project': 'my_project',
        'source_globus_endpoint': 'my_transfer_endpoint',
        'groups': []
    }


@pytest.fixture
def mock_pilot(monkeypatch):
    mock_inst = Mock()
    mock_client = Mock(return_value=mock_inst)
    mock_inst.get_globus_transfer_paths.return_value = [('/src_path', 'dest_path')]
    monkeypatch.setattr(pilot.client, 'PilotClient', mock_client)
    return mock_client


def test_publish(pilot_input, mock_pilot):
    output = publish_gather_metadata(**pilot_input)
    assert 'search' in output
    assert 'transfer' in output


def test_publish_exception(pilot_input, mock_pilot):
    mock_pilot.side_effect = PilotClientException('Something bad happened!')
    output = publish_gather_metadata(**pilot_input)
    assert 'PilotClientException' in output
    assert 'Something bad happened!' in output


def test_publish_with_public_visibility(pilot_input, mock_pilot):
    mock_pilot.return_value.get_group.return_value = 'public'
    output = publish_gather_metadata(**pilot_input)
    assert output['search']['visible_to'][0] == 'public'


def test_publish_with_private_group(pilot_input, mock_pilot):
    mock_group = str(uuid.uuid4())
    expected = f'urn:globus:groups:id:{mock_group}'
    mock_pilot.return_value.get_group.return_value = mock_group
    output = publish_gather_metadata(**pilot_input)
    assert output['search']['visible_to'][0] == expected
