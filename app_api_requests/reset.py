from google.cloud import datastore

from flask_restful import Resource
from flask import request

class Reset(Resource):
    def delete(self):
        request.get_data()
        
        # User Authentication:
        auth_header = request.headers.get('X-Authorization') # auth_header = "bearer [token]"
        token = auth_header.split()[1] # token = "[token]"
        
        # If token is in the database --> valid user
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='user')
        query.add_filter("bearerToken", "=", token)
        results = list(query.fetch())

        if len(results) == 0: # The token is NOT in the database --> Invalid user
            response = {
                'message': "Unauthorized user. Bearer Token is not in the datastore."
            }
            return response, 400
        # else, the user is in the database. Carry on.

        query = datastore_client.query(kind='package')
        results = list(query.fetch())
        ids = [datastore_client.key('package', x['ID']) for x in results]
        datastore_client.delete_multi(ids)

        return {}, 200