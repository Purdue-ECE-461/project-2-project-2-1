from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

def test_rate_package_dne():
    clear_registry()

    header = generate_header()
    
    response = requests.get('http://127.0.0.1:8080/package/dummy_id/rate', headers=header)
    assert response.status_code == 400

def test_rate_package_normal():
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "Express",
            "Version": "4.17.1",
            "ID": "express"
        },
        "data": {
            "URL": "https://github.com/expressjs/express",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201
    response = response.json()
    id = response['ID']

    response = requests.get('http://127.0.0.1:8080/package/' + id + '/rate', headers=header)
    assert response.status_code == 200

    response = response.json()
    
    metric_names = ['BusFactor', 'Correctness', 'ResponsiveMaintainer', 'LicenseScore', 'GoodPinningPractice']
    for m in metric_names:
        assert response[m] >= 0 and response[m] <= 1