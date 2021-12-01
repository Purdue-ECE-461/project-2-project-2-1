import os
from app_api_requests.datastore_client_factory import get_datastore_client

from google.cloud import datastore

import requests

def setup_test_datastore():
    # Setup the local datastore to have the authorization and tokens 
    # in its default state
    client = datastore.Client()

    query = client.query(kind='user')
    query.add_filter('name', '=', 'ece461defaultadminuser')
    user_entity = list(query.fetch())[0]

    query = client.query(kind='tokens')
    token = list(query.fetch())[0]

    client = get_datastore_client()
    client.put(user_entity)
    client.put(token)

def generate_header():
    client = get_datastore_client()

    query = client.query(kind='user')
    query.add_filter('name', '=', 'ece461defaultadminuser')

    user_entity = list(query.fetch())[0]
    auth_token = user_entity['bearerToken']

    return {'X-Authorization': 'bearer ' + auth_token}

def clear_registry():
    # Function for clearing packages in the emulator datastore
    client = get_datastore_client()
    query = client.query(kind='package')
    results = list(query.fetch())
    ids = [client.key('package', x['ID']) for x in results]
    client.delete_multi(ids)