from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest


def test_getpackages_empty_registry():
    client = get_datastore_client()
    clear_registry()
    
    header = generate_header()
    query = [{
        "Name": '*' 
    }]

    response = requests.post('http://127.0.0.1:8080/packages', headers=header, json=query)
    assert response.status_code == 200
    print(response.content)
    
"""
def test_getpackages_full_registry():
    header = generate_header()
    query = {
        "metadata": {
            "Name": "FreeCodeCamp",
            "Version": "1.0.0",
            "ID": "freeCodeCamp"
        },
        "data": {
            "Content": "",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

curl -i --location --request POST 'http://127.0.0.1:8080/package' \
--header 'X-Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c' \
--data-raw '{
	"metadata": {
		"Name": "Lodash",
		"Version": "1.2.5",
		"ID": "lodash_local"
	},
	"data": {
		"Content": "",
		"JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
	}
}'
def test_getpackages_partial_registry():
    pass
"""