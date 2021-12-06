from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

# Registering User: "200: Success"
def test_register1():
    client = get_datastore_client()
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

    assert response['Name'] == 'Express'
    assert response['Version'] == '4.17.1'
    assert response['ID'] == 'express'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'express')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'Express'
    assert package_entity['Version'] == '4.17.1'
    assert package_entity['ID'] == 'express'
    assert package_entity['Content'] == ''
    assert package_entity['URL'] == 'https://github.com/expressjs/express'

# Registering another User: "200: Success"
def test_register2():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "Debug",
            "Version": "4.3.3",
            "ID": "debug"
        },
        "data": {
            "URL": "https://github.com/debug-js/debug",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

    response = response.json()

    assert response['Name'] == 'Debug'
    assert response['Version'] == '4.3.3'
    assert response['ID'] == 'debug'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'debug')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'Debug'
    assert package_entity['Version'] == '4.3.3'
    assert package_entity['ID'] == 'debug'
    assert package_entity['Content'] == ''
    assert package_entity['URL'] == 'https://github.com/debug-js/debug'

# "401: The user uploading is NOT an Admin "
def test_register_401_not_admin():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "InversifyJS",
            "Version": "6.0.1",
            "ID": "inversifyJS"
        },
        "data": {
            "URL": "https://github.com/inversify/InversifyJS",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

    response = response.json()

    assert response['Name'] == 'InversifyJS'
    assert response['Version'] == '6.0.1'
    assert response['ID'] == 'inversifyJS'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'inversifyJS')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'InversifyJS'
    assert package_entity['Version'] == '6.0.1'
    assert package_entity['ID'] == 'inversifyJS'
    assert package_entity['Content'] == ''
    assert package_entity['URL'] == 'https://github.com/inversify/InversifyJS'

# "401: The user uploading has an invalid X-auth "
def test_register_401_wrong_XAuth():