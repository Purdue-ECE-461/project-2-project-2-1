from google.cloud import datastore

from flask_restful import Resource
from flask import request

import json
from uuid import uuid4

def print_to_stdout(*a):
    print(*a, file = sys.stdout)

class Authenticate(Resource):
    def put(self):
        request.get_data()
        
        decoded_data = request.data.decode("utf-8")
        request_body = json.loads(decoded_data)
        
        try:
            input_name = request_body['User']['name']
            input_isAdmin = request_body['User']['isAdmin']

            input_password = request_body['Secret']['password']
        except Exception:
            return {"message": "Error getting values from request body."}, 401

        datastore_client = datastore.Client()

        # Check to see if the User already exists in the registry
        query = datastore_client.query(kind='user') # LOWERCASE "user"
        query.add_filter("name", "=", input_name)
        results = list(query.fetch())

        # User DOES exist.
        # No need to generate a new auth token.
        # CHECK THE PASSWORD
        # Return the Bearer Token.
        if len(results == 1):
            # CHECK THE PASSWORD
            key = datastore_client.key('user', input_name)
            recorded_user = datastore_client.get(key)
            recorded_password = recorded_user["password"]

            if (recorded_password != input_password)
                response = {
                    "message": "Incorrect password"
                }
                return response, 401
            
            # If we get here, then the password is right.
            # Return the bearer token
            recorded_token = recorded_user["bearerToken"]
            response =  ("bearer " + recorded_token)

            return response, 200

        # User DOES NOT exist.
        else
            response = {
                "message": "Invalid User. Username is not in the Datastore."
            }
            return response, 401

        # BELOW, I create a new user ... but I think it should return an error here.
        """
            # The kind for the new entity
            kind = "user"

            # The name/ID for the new entity
            name = input_name # Use the "username" for the "name/ID"/Identifier of the Entity

            # The Cloud Datastore key for the new entity
            user_key = datastore_client.key(kind, name)

            # Prepares the new entity
            new_user = datastore.Entity(key=user_key)
            new_user["name"] = input_name
            new_user["isAdmin"] = input_isAdmin
            new_user["password"] = input_password
            token = uuid4() # generates a random auth bearer token
            # print_to_stdout("Bearer Token: " + token)
            new_user["bearerToken"] = token

            # Saves the entity
            datastore_client.put(task)
            
            response =  ("bearer " + token)
            
            return response, 200
            """