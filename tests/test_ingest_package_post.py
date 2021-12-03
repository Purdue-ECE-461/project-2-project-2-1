from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

def test_ingest_package_post_REPO1():
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

def test_ingest_package_post_REPO2():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "Prettier",
            "Version": "2.5.0",
            "ID": "prettier"
        },
        "data": {
            "URL": "https://github.com/prettier/prettier",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

    response = response.json()

    assert response['Name'] == 'Prettier'
    assert response['Version'] == '2.5.0'
    assert response['ID'] == 'prettier'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'prettier')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'Prettier'
    assert package_entity['Version'] == '2.5.0'
    assert package_entity['ID'] == 'prettier'
    assert package_entity['Content'] == ''
    assert package_entity['URL'] == 'https://github.com/prettier/prettier'


def test_ingest_package_post_REPO3():
    client = get_datastore_client()
    clear_registry()

    header = generate_header()
    query = {
        "metadata": {
            "Name": "Cross-fetch",
            "Version": "3.1.4",
            "ID": "cross-fetch"
        },
        "data": {
            "URL": "https://github.com/lquixada/cross-fetch",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
        }
    }

    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    assert response.status_code == 201

    response = response.json()

    assert response['Name'] == 'Cross-fetch'
    assert response['Version'] == '3.1.4'
    assert response['ID'] == 'cross-fetch'

    query = client.query(kind='package')
    query.add_filter("ID", "=", 'cross-fetch')
    package_entity = list(query.fetch())[0]

    assert package_entity['Name'] == 'Cross-fetch'
    assert package_entity['Version'] == '3.1.4'
    assert package_entity['ID'] == 'cross-fetch'
    assert package_entity['Content'] == ''
    assert package_entity['URL'] == 'https://github.com/lquixada/cross-fetch'


def test_ingest_package_post_REPO4():
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


def test_ingest_package_post_REPO5():
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