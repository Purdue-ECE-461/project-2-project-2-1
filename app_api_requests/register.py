from google.cloud import datastore
from app_api_requests.datastore_client_factory import get_datastore_client

from flask_restful import Resource
from flask import request
import sys
import base64

import json
import uuid
import os

def print_to_stdout(*a):
    print(*a, file = sys.stdout)

def uuid1():
    """Generate a random UUID."""
    return uuid(bytes=os.urandom(16), version=1)

# 401: Unauthorized
# 200: Successful upload of a new user
class Register(Resource):
    def put(self, current_user_name):
        request.get_data()
        
        decoded_data = request.data.decode("utf-8")
        request_body = json.loads(decoded_data)

        # Get the inputted "current_user_name" from the URL path
        current_username = request.view_args['current_user_name']

        # In order to REGISTER a NEW user, the CURRENT user must
        # (a) be authenticated using the header the provided
        # (b) isAdmin == TRUE

        # (a) Current_User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"

        # If token is in the database --> valid user
        # datastore_client = datastore.Client()
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token provided is not in the datastore."
            }
            return response, 401
        # else, the current user is in the database. Carry on.
        
        # (b) see if the Current User's: "isAdmin == true"
        key = datastore_client.key('user', current_username) # current_user_name that's provided in the parameter path
        current_user_entity = datastore_client.get(key)
        current_user_isAdmin = current_user_entity["isAdmin"]
        
        if not(current_user_isAdmin) or (current_user_isAdmin=="False") or (current_user_isAdmin=="false"): # If the current user (who's trying to upload a new user) is NOT an Admin --> Can't upload.
            response = {
                'message': "Current user is not an Admin. Therefore cannot upload a new user."
            }
            return response, 401
        # else: The current user IS an admin --> they can now upload a new_user

        try:
            new_user_name = request_body['User']['name']
            new_user_isAdmin = request_body['User']['isAdmin']

            new_user_password = request_body['Secret']['password']
        except Exception:
            response = {
                "message": "Error getting values from request body."
            }
            return response, 401


        # Create a new user
        # The kind for the new entity
        kind = 'user'

        # The name/ID for the new entity
        name = new_user_name # Use the "username" for the "name/ID"/Identifier of the Entity

        # The Cloud Datastore key for the new entity
        new_user_key = datastore_client.key(kind, name)

        # Prepares the new entity
        new_user = datastore.Entity(key=new_user_key)
        new_user['name'] = new_user_name
        new_user['isAdmin'] = str(new_user_isAdmin)
        new_user['password'] = new_user_password
        token = uuid.uuid1().hex
        new_user['bearerToken'] = token

        # Saves the entity
        datastore_client.put(new_user)
        
        response =  {
            "message": "User successfully uploaded.",
            "bearerToken": token
        }
        
        return response, 200
