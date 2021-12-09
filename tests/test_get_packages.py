from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest


def test_getpackages_empty_registry():
    client = get_datastore_client()
    clear_registry()
    
    # Make sure an empty registry responds to requests correctly

    header = generate_header()
    query = [{
        "Name": '*' 
    }]
    # Start with full registry request, with no offset    
    response = requests.post('http://127.0.0.1:8080/packages', headers=header, json=query)
    assert response.status_code == 200
    # Same request, except for an offset in URL below
    response = requests.post('http://127.0.0.1:8080/packages?offset=10', headers=header, json=query)
    assert response.status_code == 200
    
    # Now request partial registry
    query = [{
        "Version": "1.2.3",
        "Name": "Underscore"
    },
    {
        "Version": "1.2.3-2.1.0",
        "Name": "Lodash"
    }]
    response = requests.post('http://127.0.0.1:8080/packages', headers=header, json=query)
    assert response.status_code == 200
    # Same request, except for an offset in URL below
    response = requests.post('http://127.0.0.1:8080/packages?offset=10', headers=header, json=query)
    assert response.status_code == 200    
    
def test_getpackages_full_registry():
    client = get_datastore_client()
    clear_registry()
    # First populate the registry with some packages (they only need Name/Version/ID)
    header = generate_header()
    
    # Add Underscore
    query = {
    "metadata": {
            "Name": "Underscore",
            "Version": "1.0.1",
            "ID": "underscore_local"
    },
    "data": {
            "Content": "",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add Lodash
    query = {
    "metadata": {
            "Name": "Lodash",
            "Version": "1.2.5",
            "ID": "lodash_local"
    },
    "data": {
            "Content": "",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add netdata
    query = {
    "metadata": {
            "Name": "Netdata",
            "Version": "1.0.0",
            "ID": "netdata"
    },
    "data": {
            "URL": "https://github.com/netdata/netdata",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add debug
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
    #assert response.status_code == 201
    
    # Now try to use get_packages to query the datastore
    #header = generate_header()
    query = [{
            "Name": "*"
            }]

    response = requests.post('http://127.0.0.1:8080/packages', headers=header, json=query)
    assert response.status_code == 200

def test_getpackages_partial_registry():
    client = get_datastore_client()
    clear_registry()
    # First populate the registry with some packages (they only need Name/Version/ID)
    header = generate_header()
    
    # Add Underscore
    query = {
    "metadata": {
            "Name": "Underscore",
            "Version": "1.0.1",
            "ID": "underscore_local"
    },
    "data": {
            "Content": "",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add Lodash
    query = {
    "metadata": {
            "Name": "Lodash",
            "Version": "1.2.5",
            "ID": "lodash_local"
    },
    "data": {
            "Content": "",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add netdata
    query = {
    "metadata": {
            "Name": "Netdata",
            "Version": "1.0.0",
            "ID": "netdata"
    },
    "data": {
            "URL": "https://github.com/netdata/netdata",
            "JSProgram": "if (process.argv.length === 7) {\nconsole.log('\''Success'\'')\nprocess.exit(0)\n} else {\nconsole.log('\''Failed'\'')\nprocess.exit(1)\n}\n"
    }
    }
    response = requests.post('http://127.0.0.1:8080/package', headers=header, json=query)
    #assert response.status_code == 201
    
    # Add debug
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
    #assert response.status_code == 201        
    
    # Now try to use get_packages to query the datastore
    #header = generate_header()
    query = [{
        "Version": "1.2.3",
        "Name": "Underscore"
    },
    {
        "Version": "1.2.3-2.1.0",
        "Name": "Lodash"
    }]
    response = requests.post('http://127.0.0.1:8080/packages', headers=header, json=query)
    assert response.status_code == 200