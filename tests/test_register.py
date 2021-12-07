from app_api_requests.datastore_client_factory import get_datastore_client
from tests.test_utils import setup_test_datastore, generate_header, clear_registry
import requests
import pytest

# "ece461defaultadminuser" is registering "newUser" --> "200: Success"
def test_register_200():
    client = get_datastore_client()

    header = generate_header()
    query = {
        "User": {
            "name": "newUser",
            "isAdmin": True
        },
        "Secret": {
            "password": "newUserPassword"
        }
    }

    response = requests.put('http://127.0.0.1:8080/register/ece461defaultadminuser', headers=header, json=query)
    assert response.status_code == 200

    response = response.json()

    query = client.query(kind='user')
    query.add_filter("name", "=", "newUser")
    user_entity = list(query.fetch())[0]

    assert user_entity['name'] == "newUser"
    assert user_entity['isAdmin'] == "True"
    assert user_entity['password'] == 'newUserPassword'
    assert user_entity['bearerToken'] != '' # Assert that the field isn't blank, and a token was assigned



# "401: The user uploading is NOT an Admin "
def test_register_401_not_admin():
    client = get_datastore_client()

    # ece461defaultadminuser is registering this NON-ADMIN user
    header = generate_header()
    query = {
        "User": {
            "name": "newUser1",
            "isAdmin": False
        },
        "Secret": {
            "password": "newUser1Password"
        }
    }

    response = requests.put('http://127.0.0.1:8080/register/ece461defaultadminuser', headers=header, json=query)
    assert response.status_code == 200

    # Now, "newUser1" (NOT admin) is registering "newUser2" (is an admin)
    # get "newUser1"'s header:
    query = client.query(kind='user')
    query.add_filter('name', '=', 'newUser1')
    user_entity = list(query.fetch())[0]

    auth_token = user_entity['bearerToken']
    header = {'X-Authorization': 'bearer ' + auth_token}

    # "newUser1" (NOT admin) is registering "newUser2"
    query = {
        "User": {
            "name": "newUser2",
            "isAdmin": False
        },
        "Secret": {
            "password": "newUser2Password"
        }
    }

    response = requests.put('http://127.0.0.1:8080/register/newUser1', headers=header, json=query)
    assert response.status_code == 401

# "401: The user uploading ("ece461defaultadminuser") has an invalid X-auth "
def test_register_401_wrong_XAuth():
    client = get_datastore_client()

    # WRONG auth token of the "uploader"
    header = {'X-Authorization': 'bearer ' + "invalid_auth_token"}
    query = {
        "User": {
            "name": "newUser",
            "isAdmin": False
        },
        "Secret": {
            "password": "newUserPassword"
        }
    }

    response = requests.put('http://127.0.0.1:8080/register/ece461defaultadminuser', headers=header, json=query)
    assert response.status_code == 401