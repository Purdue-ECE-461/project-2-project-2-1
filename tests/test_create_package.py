from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

def test_create_new_package_with_url():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "Underscore",
            "Version": "1.0.1",
            "ID": "underscore_local"
        },
        "data": {
            "Content": "content",
            "URL": "https://github.com/jashkenas/underscore",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

    response = response.json()

    assert response['Name'] == 'Underscore'
    assert response['Version'] == '1.0.1'
    assert response['ID'] == 'underscore_local'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'underscore_local')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'Underscore'
    assert package_entity['Version'] == '1.0.1'
    assert package_entity['ID'] == 'underscore_local'
    assert package_entity['Content'] == 'content'
    assert package_entity['URL'] == 'https://github.com/jashkenas/underscore'