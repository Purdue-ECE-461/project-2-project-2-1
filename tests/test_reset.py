from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest


def test_empty_reset():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    
    response = requests.delete('http://127.0.0.1:8080/reset', headers=header)
    assert response.status_code == 200

    query = client.query(kind='package')
    packages = list(query.fetch())

    assert len(packages) == 0

def test_non_empty_reset():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()

    # add an item to the registry
    query = {
        "metadata": {
            "Name": "FreeCodeCamp",
            "Version": "1.0.0",
            "ID": "freeCodeCamp"
        },
        "data": {
            "Content": "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",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    requests.post('http://127.0.0.1:8080/package', headers=header, json=query)

    response = requests.delete('http://127.0.0.1:8080/reset', headers=header)
    assert response.status_code == 200

    query = client.query(kind='package')
    packages = list(query.fetch())

    assert len(packages) == 0

def test_bad_credentials():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()

    # add an item to the registry
    query = {
        "metadata": {
            "Name": "FreeCodeCamp",
            "Version": "1.0.0",
            "ID": "freeCodeCamp"
        },
        "data": {
            "Content": "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",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    requests.post('http://127.0.0.1:8080/package', headers=header, json=query)

    header = {}

    response = requests.delete('http://127.0.0.1:8080/reset', headers=header)
    assert response.status_code == 401
    response = response.json
    assert response['message'] == "Unauthorized user. Bearer Token is not in the datastore."

    query = client.query(kind='package')
    packages = list(query.fetch())

    assert len(packages) == 1