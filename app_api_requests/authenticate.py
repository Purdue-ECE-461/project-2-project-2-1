from google.cloud import datastore
from app_api_requests.datastore_client_factory import get_datastore_client

from flask_restful import Resource
from flask import request
import sys

import json

import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)

def print_to_stdout(*a):
    print(*a, file = sys.stdout)

class Authenticate(Resource):
    def put(self):
        logger.info('Executing PUT /authenticate endpoint...')
        logger.info('Getting request data...')
        request.get_data()
        
        decoded_data = request.data.decode("utf-8")
        request_body = json.loads(decoded_data)
        logger.info(request_body)
        
        try:
            input_name = request_body['User']['name']
            input_isAdmin = request_body['User']['isAdmin']

            input_password = request_body['Secret']['password']
        except Exception:
            logger.error("Error getting values from request body.")
            response = {
                "message": "Error getting values from request body."
            }
            return response, 401

        datastore_client = get_datastore_client()

        # Check to see if the User already exists in the registry
        query = datastore_client.query(kind='user') # LOWERCASE "user"
        query.add_filter("name", "=", input_name)
        results = list(query.fetch())

        # User DOES exist.
        # No need to generate a new auth token.
        # CHECK THE PASSWORD
        # Return the Bearer Token.
        if len(results) == 1:
            # CHECK THE PASSWORD
            key = datastore_client.key('user', input_name)
            recorded_user = datastore_client.get(key)
            recorded_password = recorded_user["password"]

            if (recorded_password != input_password):
                logger.error("Password inputted in request: "+input_password +" Does not match Password in datastore/on record: "+ recorded_password )
                response = {
                    "message": "Incorrect password"
                }

                return response, 401
            
            # If we get here, then the password is right.
            logger.info("Correct password. The password provided matches password in datastore.")
            # Return the bearer token
            recorded_token = recorded_user["bearerToken"]
            response =  ("bearer " + recorded_token)

            return response, 200

        # User DOES NOT exist.
        else:
            logger.error("Username inputted in request: "+ str(input_name) +", is not in datastore/on record.")
            response = {                
                "message": "Invalid User. Username is not in the Datastore."
            }
            return response, 401