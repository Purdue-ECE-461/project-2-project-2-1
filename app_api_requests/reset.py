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
        logger.info(request.get_data())
        
        # User Authentication:
        try:
            auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
            logger.info('X-Authorization was included. Getting bearer token...')
            token = auth_header.split()[1] # token = "[token]"
            logger.info('Token: ' + token)
        except Exception:
            # User didn't include authorization in their request
            logger.error('X-Authorization was NOT included in the request.')
            response = {
                'message': "X-Authorization / Bearer Token was NOT included in the request.",
            }
            return response, 401
        
        # If token is in the database --> valid user
        datastore_client = get_datastore_client()
        query = datastore_client.query(kind='user')
        results = list(query.fetch())
        logger.info('Number of users: ' + str(len(results)))
        
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())
        logger.info('Number of users with matching tokens: ' + str(len(results)))

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            logger.error('Token: ' + token + ' does not match any registered users.')
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 401
        # else, the user is in the database. Carry on.

        logger.info('Clearing registry of all packages...')
        query = datastore_client.query(kind='package')
        results = list(query.fetch())
        ids = [datastore_client.key('package', x['ID']) for x in results]
        datastore_client.delete_multi(ids)
        logger.info('Package-Registry cleared')

        logger.info('Clearing registry of all users...')
        query = datastore_client.query(kind='user')
        results = list(query.fetch())
        logger.info('Fetching the current users in the database to delete...')
        logger.info(results)
        ids = [datastore_client.key('user', x['name']) for x in results ] # if (x['name'] is not "ece461defaultadminuser")]
    
        # Don't delete the admin-user. Remove from the list of user-ids-to-delete
        save_key = datastore_client.key('user', "ece461defaultadminuser")
        ids.remove( save_key )

        logger.info('Deleting users from the database...')
        logger.info('ece461defaultadminuser not included in the deletion')
        logger.info(ids)

        # Now delete
        datastore_client.delete_multi(ids)
        logger.info('User-Registry cleared. ece461defaultadminuser still there.')
        

        return {}, 200