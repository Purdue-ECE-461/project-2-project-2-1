from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

def test_existing_user_auth():
    client = get_datastore_client()
    clear_registry()
    

    query = {
        "User": {
            "name": "ece461defaultadminuser",
            "isAdmin": True
        },
        "Secret": {
            "password": "correcthorsebatterystaple123(!__+@**(A"
        }
    }
    
    response = requests.put('http://127.0.0.1:8080/authenticate', json=query)

    assert response.status_code == 200
    assert len(response.text) > 0

def test_nonexisting_user_auth():
    client = get_datastore_client()
    clear_registry()
    

    query = {
        "User": {
            "name": "dummy_user",
            "isAdmin": True
        },
        "Secret": {
            "password": "dummy_password"
        }
    }
    
    response = requests.put('http://127.0.0.1:8080/authenticate', json=query)

    assert response.status_code == 401

def test_incorrect_password():
    client = get_datastore_client()
    clear_registry()
    

    query = {
        "User": {
            "name": "ece461defaultadminuser",
            "isAdmin": True
        },
        "Secret": {
            "password": "dummy_password(!__+@**(A"
        }
    }
    
    response = requests.put('http://127.0.0.1:8080/authenticate', json=query)

    assert response.status_code == 401
    
    response = response.json()
    assert response['message'] == "Incorrect password"