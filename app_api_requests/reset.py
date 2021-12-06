from google.cloud import datastore

from flask_restful import Resource
from flask import request

from app_api_requests.datastore_client_factory import get_datastore_client

import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
logger = logging.getLogger(__name__)

class Reset(Resource):
    def delete(self):
        logger.info('Executing /reset endpoint...')
        logger.info('Getting request data...')
        request.get_data()
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        logger.info('Token: ' + token)
        
        # If token is in the database --> valid user
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())
        logger.info('Number of users with matching tokens: ' + str(len(results)))

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            logger.error('Token: ' + token + ' does not match any registered users.')
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 400
        # else, the user is in the database. Carry on.

        logger.info('Clearing registry of all packages...')
        query = datastore_client.query(kind='package')
        results = list(query.fetch())
        ids = [datastore_client.key('package', x['ID']) for x in results]
        datastore_client.delete_multi(ids)

        logger.info('Registry cleared')
        return {}, 200